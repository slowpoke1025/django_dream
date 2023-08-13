# from django.shortcuts import render
from datetime import datetime, timedelta
import os
import random
from accounts.models import User
from api.utils.ethereum import mint_test, read_test
from .models import Thing, Gear, Exercise, Wear, WeekTask
from accounts.permissions import IsOwnerOrAdmin, IsUserOrAdmin
from django.db import transaction
from django.db.models import Sum, Value, F
from django.http import Http404
from django.db.models.functions import Coalesce
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound


from .serializers import (
    GearSerializers,
    MintSerializers,
    ThingSerializers,
    ExerciseSerializers,
    WearSerializers,
    WearUpdateSerializers,
)


class BagView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        things = user.thing_set.all().exclude(amount=0).order_by("type")
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
        things = user.thing_set.all().exclude(amount=0).order_by("type")
        serializer = ThingSerializers(things, many=True)
        return Response(serializer.data)


class GearView(ModelViewSet):
    permission_classes = [IsOwnerOrAdmin]
    serializer_class = MintSerializers
    lookup_field = "token_id"

    def get_queryset(self):
        if self.action == "list":
            return Gear.objects.filter(user=self.request.user)
        else:
            return Gear.objects.all()

    def create(self, request, *args, **kwargs):
        address = request.user.address
        serializer = MintSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lucky = self.generate_lucky(data.get("lucky"))

        try:
            res = mint_test(address)
        except Exception as err:
            print("error:", err)
            return Response({"error": type(err).__name__}, status=401)

        status = res.pop("status", None)
        token_id = res.pop("token_id")

        if not status:
            return Response({"error": "mint error"}, status=400)

        gear = serializer.save(user=request.user, token_id=token_id, lucky=lucky)
        return Response(
            {"tx": res, "uri": gear.uri, "gear": {**serializer.data}}, status=200
        )

    def generate_lucky(self, type):
        lucky_choices = [type, "epic"]
        lucky_weights = [1 - Gear.PROB_EPIC[type], Gear.PROB_EPIC[type]]
        _type = random.choices(lucky_choices, weights=lucky_weights)[0]
        _range = Gear.LUCKY_RANGE[_type]
        lucky = random.randint(_range[0] * 100, _range[1] * 100) / 100
        # return math.floor(random.uniform(lower, upper) * 100) / 100  # exclusive
        return lucky

    # def retrieve(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #         serializer = self.get_serializer(instance)
    #         return Response(serializer.data, status=200)
    #     except Exception as err:
    #         print(err)
    #         raise NotFound("Object not found.")

    # def list(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data, status=200)

    # def get(self, request, pk=None):
    #     user = request.user
    #     if pk == None:
    #         gears = user.gear_set.all().order_by("type", "level")
    #         serializer = GearSerializers(gears, many=True)
    #         return Response(serializer.data)
    #     else:
    #         try:
    #             gear = user.gear_set.get(pk=pk)
    #             serializer = GearSerializers(gear)
    #             return Response(serializer.data, status=200)
    #         except Gear.DoesNotExist:
    #             return Response({'message': 'Gear not found'}, status=404)

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

    def handle_thing(self, request, data):  # type 轉成string, 待改
        thing_level = data.get("thing")
        if thing_level == None:
            return None, 1

        thing = Thing.objects.filter(user=request.user, type=thing_level).first()
        if not thing or thing.amount == 0:
            raise PermissionDenied("You don't have any thing of given type")

        thing.amount -= 1
        thing.save()

        bonus = Thing.weights.get(thing_level, 1)

        return ThingSerializers(thing).data, bonus

    @transaction.atomic  # # transaction.set_rollback(True)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # gear = data.get("gear")
        count = data.get("count")
        accuracy = data.get("accuracy")
        today = datetime.now().date()

        # if gear.user != request.user:
        #     raise PermissionDenied("You are not allowed to modify this gear.")

        gear = request.user.wear.target
        if gear is None:
            raise PermissionDenied("You haven't set the target gear !")

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
        serializer.save(gear=gear)

        return Response(
            {
                "exp": exp,
                **serializer.data,
                "gear": {
                    "token_id": gear.token_id,
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
            .values("type")
            .annotate(total_count=Sum("count"))
        )

        print(exercises)
        result_data = {
            item["type"]: {"count": item["total_count"]} for item in exercises
        }

        result = [{"type": type[1], "count": 0} for type in Exercise.Type.choices]
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
        probabilities = Thing.probabilities

        # 根據機率隨機獲取一個等級
        choices = [*probabilities.keys()]
        values = [*probabilities.values()]
        level = random.choices(choices, weights=values)[0]

        # 檢查是否已經有同一等級的thing存在
        existing_thing = Thing.objects.filter(user=request.user, type=level).first()

        if existing_thing:
            # 如果已存在，將amount加一
            existing_thing.amount += 1
            existing_thing.save()
            new_thing = existing_thing
        else:
            # 否則創建新的thing
            new_thing = Thing.objects.create(user=request.user, type=level)
            new_thing.amount = 1
            new_thing.save()

        # 返回結果
        response_data = {
            "message": "You got a new thing x 1",
            "type": new_thing.type,
            "amount": new_thing.amount,
        }
        return Response(response_data)


class WearView(ModelViewSet):
    permission_classes = [IsAuthenticated]

    serializer_class = WearUpdateSerializers
    lookup_field = "token_id"

    def get_queryset(self):
        return self.request.user.gear_set

    # def get_object(self):
    #     token_id = self.kwargs.get("token_id")
    #     if self.request.method == "PUT":
    #         serializer = self.get_serializer(data=self.request.data)
    #         serializer.is_valid(raise_exception=True)
    #         token_id = serializer.data.get("token_id")

    #     gear = self.get_queryset().filter(token_id=token_id).first()
    #     if gear is None:
    #         raise PermissionDenied(
    #             f"You are not allowed to modify this gear ({token_id})"
    #         )
    #     return gear
    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {"detail": "You are not allowed to modify this gear"}, status=403
            )

        return super().handle_exception(exc)

    def update(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear

        if getattr(wear, gear.pos) == gear:
            raise PermissionDenied("This gear is already dressed")

        setattr(wear, gear.pos, gear)
        wear.save()
        return Response(
            {"message": f"Update successfully", "dress": wear.dress}, status=200
        )

    def _update(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear
        if wear.target == gear:
            raise PermissionDenied("This gear is already targeted")
        wear.target = gear
        wear.save()
        return Response(
            {"message": f"Update target successfully", "target": wear.target.token_id},
            status=200,
        )

    def destroy(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear

        if getattr(wear, gear.pos) != gear:
            raise PermissionDenied("This gear isn't dressed.")

        setattr(wear, gear.pos, None)
        wear.save()
        return Response(
            {"message": f"Undress successfully", "dress": wear.dress}, status=200
        )

    # def perform_update(self, serializer):
    #     # Ensure the wear object belongs to the authenticated user
    #     instance = serializer.instance
    #     if instance.user != self.request.user:
    #         return Response({"error": "You are not allowed to update this wear object."},
    #                         status=403)


#    def update(self, request, *args, **kwargs):
#         partial = kwargs.pop("partial", False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response(
#             {"message": "updated successfully", "data": serializer.data}, status=200
#         )

#     def partial_update(self, request, *args, **kwargs):
#         kwargs["partial"] = True
#         return self.update(request, *args, **kwargs)


class readView(APIView):
    def get(self, request):
        try:
            res = read_test(request.user.address)
            return Response(res, status=200)
        except Exception as err:
            print(err)
            return Response({"error": str(err)}, status=400)


# class mintView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         address = request.user.address
#         serializer = MintSerializers(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         res = mint_test(address)

#         if res["tx"].get("status"):
#             lucky_probabilities = {0: 0.4, 1: 0.3, 2: 0.2, 3: 0.1}
#             lucky_choices = list(lucky_probabilities.keys())
#             lucky_weights = list(lucky_probabilities.values())
#             lucky = random.choices(lucky_choices, weights=lucky_weights)[0]
#             gear = serializer.save(
#                 user=request.user, token_id=res["token_id"], lucky=lucky
#             )

#             return Response({"tx": res["tx"], "gear": serializer.data}, status=200)

#         return Response({"error": "mint error"}, status=400)
