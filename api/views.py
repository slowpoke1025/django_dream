# from django.shortcuts import render
from datetime import datetime, timedelta
import os
import random
from accounts.models import User
from api.utils.ethereum import mint_test, read_test
from .models import Thing, Gear, Exercise, WeekTask
from accounts.permissions import IsUserOrAdmin
from django.db import transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    GearSerializers,
    ThingSerializers,
    ExerciseSerializers,
)


class BagView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        things = user.thing_set.all().order_by("level")
        gears = user.gear_set.all().order_by("type", "level")
        thing_serializer = ThingSerializers(things, many=True)
        gear_serializer = GearSerializers(gears, many=True)
        return Response(
            {"gears": gear_serializer.data, "things": thing_serializer.data}
        )


class ThingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        things = user.thing_set.all().order_by("level")
        serializer = ThingSerializers(things, many=True)
        return Response(serializer.data)


class GearView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        gears = user.gear_set.all().order_by("type", "level")
        serializer = GearSerializers(gears, many=True)
        return Response(serializer.data)

    # class GearView(ModelViewSet):
    #     queryset = Gear.objects.all()
    #     serializer_class = GearSerializers
    #     permission_classes = [IsAuthenticated]

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)


class ExerciseView(ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializers
    permission_classes = [IsAuthenticated]

    def handle_task(self, exercise, user):
        if exercise.exists():
            return None
        today = datetime.now().date()
        task = user.task
        delta = today - task.week_start

        if delta == timedelta(days=task.count - 1):  # 已完成
            return None

        if delta == timedelta(days=task.count) and task.count != 0:  # 連續
            task.count += 1
            if task.count >= 7:
                message = "恭喜完成每周任務!"
                status = "WEEKLY_COMPLETE"
            else:
                message = "完成本日任務"
                status = "DAILY_COMPLETE"
        else:  # delta > timedelta(days=task.count)
            task.week_start = today
            task.count = 1
            message = "完成首日任務"
            status = "DAILY_COMPLETE"

        task.save()  # 保存更新後的 WeekTask
        return {"message": message, "status": status, "count": task.count}

    def handle_thing(self, request, data):
        thing_level = data.get("thing_level")
        if thing_level == None:
            return None, 1

        thing = Thing.objects.filter(user=request.user, level=thing_level).first()
        if not thing or thing.amount == 0:
            raise PermissionDenied("You don't have any thing of specified level")

        thing.amount -= 1
        thing.save()

        bonus_table = {k: v for k, v in enumerate([1.25, 1.5, 1.75])}
        bonus = bonus_table.get(thing_level, 1)

        return ThingSerializers(thing).data, bonus

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        gear = data.get("gear")
        count = data.get("count")
        accuracy = data.get("accuracy")
        today = datetime.now().date()

        if gear.user != request.user:
            raise PermissionDenied("You are not allowed to modify this gear.")

        daily_exercise = Exercise.objects.filter(
            timestamp__date=today, gear__user=gear.user
        )

        total_count = (
            daily_exercise.filter(
                gear=gear,
            ).aggregate(total=Coalesce(Sum("count"), Value(0)))
        )["total"]

        if total_count >= gear.work_max:
            raise PermissionDenied(
                "You have already reached the maximum exp for this gear today"
            )

        count = min(count, gear.work_max - total_count)
        thing, bonus = self.handle_thing(request, data)
        task = self.handle_task(daily_exercise, gear.user)

        exp = count * bonus * accuracy
        gear.exp += exp
        gear.save()
        serializer.save()

        return Response(
            {
                "exp": exp,
                **serializer.data,
                "gear": {
                    "id": gear.id,
                    "exp": gear.exp,
                    "daily_count": min(total_count + count, gear.work_max),
                },
                "task": task,
                "thing": thing,
            },
            status=201,
        )

    # def perform_create(self, serializer):  #
    #     data = serializer.validated_data
    #     gear = data.get("gear")
    #     accuracy = data.get("accuracy")  # or from server
    #     count = data.get("count")

    #     if gear.user != self.request.user:
    #         raise PermissionDenied("You are not allowed to modify this gear.")

    #     gear.exp += accuracy  # calculate exp with exercise...
    #     gear.save()

    #     serializer.save()


class ExerciseDayView(APIView):  # 使用者每日運動種類與次數 目前是直接加總
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month, day):
        exercises = (
            Exercise.objects.filter(
                gear__user=request.user,
                timestamp__year=year,
                timestamp__month=month,
                timestamp__day=day,
            )
            .values("gear__type")
            .annotate(total_count=Sum("count"))
        )

        result_data = {
            item["gear__type"]: {"count": item["total_count"]} for item in exercises
        }
        result = [{"type": type[1], "count": 0} for type in Gear.Type.choices]
        for k, v in result_data.items():
            result[k]["count"] = v["count"]

        return Response({"empty": not len(exercises), "records": result})


class ExerciseMonthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month):  # 抓取特定user以及當前月份完成運動的紀錄
        exercises = (
            Exercise.objects.filter(
                gear__user=request.user,
                timestamp__year=year,
                timestamp__month=month,
            ).dates(
                "timestamp",
                "day",
            )
            # .values_list("timestamp__day", flat=True)
        )

        print(exercises)

        return Response(list(exercises))


class ExerciseWeekView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # 抓取特定user以及當前月份完成運動的紀錄
        task = request.user.task
        today = datetime.now().date()

        if task.delta > timedelta(days=task.count) or task.delta >= timedelta(days=7):
            task.week_start = today
            task.count = 0
            task.save()
        # exercise_days = Exercise.objects.filter(timestamp__range=(start, end))
        days = [
            {"date": task.week_start + timedelta(i), "done": i < task.count}
            for i in range(7)
        ]

        return Response({"dates": days, "count": task.count})


class GachaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 設定各等級小物的機率值
        level_probabilities = {
            0: 0.6,
            1: 0.3,
            2: 0.1,
        }

        # 根據機率隨機獲取一個等級
        level_choices = list(level_probabilities.keys())
        level_probabilities_values = list(level_probabilities.values())
        random_level = random.choices(
            level_choices, weights=level_probabilities_values
        )[0]

        # 檢查是否已經有同一等級的thing存在
        existing_thing = Thing.objects.filter(
            user=request.user, level=random_level
        ).first()

        if existing_thing:
            # 如果已存在，將amount加一
            existing_thing.amount += 1
            existing_thing.save()
            new_thing = existing_thing
        else:
            # 否則創建新的thing
            new_thing = Thing.objects.create(user=request.user, level=random_level)
            new_thing.amount = 1
            new_thing.save()

        # 返回結果
        response_data = {
            "message": "You got a new thing x 1",
            "level": new_thing.level,
            "name": new_thing.get_level_display(),
            "amount": new_thing.amount,
        }
        return Response(response_data)


class readView(APIView):
    def get(self, request):
        try:
            res = read_test()
            return Response({"data": res}, status=200)
        except Exception as err:
            return Response({"error": str(err)}, status=400)


class mintView(APIView):
    def post(self, request):
        try:
            address = request.data.get("address", os.environ.get("PUBLIC_ADDRESS"))
            receipt = mint_test(address)
            return Response({"receipt": receipt}, status=200)

        except Exception as err:
            return Response({"error": str(err)}, status=400)
