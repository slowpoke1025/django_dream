# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from datetime import timedelta, datetime
import json
import os
from django.db import models
from django.utils import timezone
from accounts.models import User


class Gear(models.Model):
    ORIENTATION = {"髮型": "healthy", "上衣": "healthy", "下著": "workout", "鞋子": "workout"}

    CONFIG = {
        "healthy": {
            "WORK_MAX": [40, 50, 60],
            "WORK_MIN": [20, 30, 40],
            "GOAL_DAYS": 14,
        },
        "workout": {
            "WORK_MAX": [60, 70, 80],
            "WORK_MIN": [40, 50, 60],
            "GOAL_DAYS": 14 / 2,
        },
    }

    class Lucky(models.IntegerChoices):
        A = (0, "regular")
        B = (1, "advanced")
        C = (2, "high-end")
        D = (3, "epic")

    class Level(models.IntegerChoices):
        A = (0, "basic")
        B = (1, "intermediate")
        C = (2, "advanced")

    with open(
        os.path.join(os.path.dirname(__file__), "gear_type.json"), "r", encoding="utf-8"
    ) as file:
        TYPES = json.load(file)

    Type = models.TextChoices(
        "Type", [(f"{k}/{v['type']}", k) for k, v in TYPES.items()]  # (display, value)
    )

    # primary_key = True in production
    token_id = models.PositiveIntegerField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(choices=Level.choices)
    type = models.CharField(max_length=10, choices=Type.choices)
    lucky = models.PositiveIntegerField(choices=Lucky.choices, default=Lucky.A)
    exp = models.FloatField(default=0)
    coupon = models.TextField(blank=True, null=True)
    custom = models.TextField(blank=True, null=True)

    @property
    def config(self):
        return self.CONFIG.get(self.orientation)

    @property
    def orientation(self):
        return self.ORIENTATION.get(self.get_type_display().split("/")[1])

    @property
    def work_max(self):
        return self.config.get("WORK_MAX")[self.level]

    @property
    def work_min(self):
        return self.config.get("WORK_MIN")[self.level]

    @property
    def goal_days(self):
        return self.config.get("GOAL_DAYS")

    @property
    def goal_exp(self):
        return self.work_max * 2 * self.goal_days

    @property
    def daily_exp(self):  # 待補
        return 0

    @property
    def max_exp(self):
        return self.goal_exp / self.goal_days

    @property
    def is_exchangable(self):
        return not self.is_redeemed and self.exp >= self.goal_exp  # 待補滿級判斷邏輯

    @property
    def is_redeemed(self):
        return self.coupon != None

    @property
    def uri(self):
        return f"http://140.117.71.159:8000/api/gears/{self.token_id}"

    def __str__(self):
        return f"{self.user.username}_{self.token_id}"

    class Meta:
        managed = True
        db_table = "gear"


# Gear.load_type()


# [Gear.Type.choices.append((k, v["name"])) for k, v in Gear.TYPES.items()]
# print("before", Gear.Type.choices)


class Exercise(models.Model):
    class Type(models.IntegerChoices):  # Gear.Type.choices
        A = (0, "二頭彎舉")
        B = (1, "伏地挺身")
        C = (2, "深蹲")

    gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
    type = models.PositiveIntegerField(choices=Type.choices, default=Type.A)
    timestamp = models.DateTimeField(auto_now_add=False, default=timezone.now)
    count = models.PositiveIntegerField(default=0)  # new
    accuracy = models.FloatField(default=0.0)

    @property
    def user(self):
        return self.gear.user

    class Meta:
        managed = True
        db_table = "exercise"

    def __str__(self):
        return f"{self.gear.user}_{self.timestamp.date()}"


class Thing(models.Model):
    class Level(models.IntegerChoices):
        BASIC = (0, "初級小物")
        INTERMEDIATE = (1, "中級小物")
        HIGH_END = (2, "高級小物")

    level = models.PositiveIntegerField(choices=Level.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # directly record amount, easy to handle
    amount = models.PositiveIntegerField(default=0)

    class Meta:
        managed = True
        db_table = "thing"
        unique_together = (("user", "level"),)

    def __str__(self):
        return f"{self.user.username}_{self.get_level_display()}"


class WeekTask(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="task"
    )
    week_start = models.DateField(auto_now=False, default=timezone.now)  # 記錄每周任務開始日期
    count = models.PositiveIntegerField(default=0)  # 記錄每周完成次數
    # last_completed = models.DateField(null=True, blank=True)  # 記錄用戶上次完成日期

    @property
    def last_completed(self):
        return self.week_start + timedelta(days=self.count - 1) if self.count else None

    @property
    def delta(self):
        return datetime.now().date() - self.week_start

    class Meta:
        managed = True

    def __str__(self):
        return f"{self.user.username}_{self.pk}"
