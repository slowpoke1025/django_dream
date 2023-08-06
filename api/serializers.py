from .models import Thing, Gear, Exercise
from rest_framework import serializers


class ThingSerializers(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["level", "name", "amount"]

    def get_name(self, obj):
        return obj.get_level_display()


class MintSerializers(serializers.ModelSerializer):
    exp = serializers.ReadOnlyField()
    token_id = serializers.ReadOnlyField()
    coupon = serializers.ReadOnlyField()
    lucky = serializers.ReadOnlyField(source="get_lucky_display")

    class Meta:
        model = Gear
        fields = [
            "token_id",
            # "uri",
            "type",
            "orientation",
            "level",
            "lucky",
            "exp",
            "goal_exp",
            "max_exp",
            "daily_exp",
            "custom",
            "coupon",
        ]


class GearSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, source="user.address")
    # type = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    # color = serializers.SerializerMethodField()

    class Meta:
        model = Gear
        fields = "__all__"
        # exclude = ["user"]

    # def get_type(self, obj):
    #     return {
    #         "value": obj.type,
    #         "name": obj.get_type_display(),
    #     }

    def get_level(self, obj):
        return obj.get_level_display()


class ExerciseSerializers(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(read_only=True)
    thing_level = serializers.IntegerField(write_only=True, required=False)
    # user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Exercise
        exclude = ["id"]

    def validate_accuracy(self, value):
        if value > 1 or value < 0:
            raise serializers.ValidationError("accuracy must be between 0 and 1")
        return value

    def create(self, validated_data):
        thing_level = validated_data.pop("thing_level", None)
        exercise = Exercise.objects.create(**validated_data)

        return exercise
