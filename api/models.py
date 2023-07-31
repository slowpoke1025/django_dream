# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from datetime import timedelta, datetime
from django.db import models
from django.utils import timezone
from accounts.models import User


class Gear(models.Model):
    class Level(models.IntegerChoices):
        A = (0, "BASIC")
        B = (1, "INTERMEDIATE")
        C = (2, "ADVANCED")

    class Color(models.IntegerChoices):
        A = (0, "STYLE_A")
        B = (1, "STYLE_B")
        C = (2, "STYLE_C")

    class Type(models.IntegerChoices):  # Gear.Type.choices
        A = (0, "上衣/二頭彎舉")
        B = (1, "下著/伏地挺身")
        C = (2, "鞋子/深蹲")

    # primary_key = True in production
    # token_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(choices=Level.choices)
    type = models.PositiveIntegerField(choices=Type.choices, blank=True)
    color = models.PositiveIntegerField(choices=Color.choices, blank=True)
    work_max = models.IntegerField(blank=True, null=True)
    exp = models.FloatField(default=0, blank=True)
    lucky = models.FloatField(blank=True, null=True)
    coupon = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}_{self.id}"

    @property
    def is_exchangable(self):
        return not self.is_redeemed and self.exp >= 0  # 待補滿級判斷邏輯

    @property
    def is_redeemed(self):
        return self.coupon != None

    class Meta:
        managed = True
        db_table = "gear"


class Exercise(models.Model):
    gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=False, default=datetime.now)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)  # new
    accuracy = models.FloatField(default=0.0)

    @property
    def user(self):
        return self.gear.user

    @property
    def type(self):
        return self.gear.get_type_display()

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
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
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
