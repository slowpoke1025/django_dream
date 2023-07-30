from .models import Thing, Gear, Exercise
from rest_framework import serializers


class ThingSerializers(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["level", "amount"]

    def get_level(self, obj):
        return obj.get_level_display()


class GearSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exp = serializers.FloatField(read_only=True)

    class Meta:
        model = Gear
        fields = "__all__"


class ExerciseSerializers(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(read_only=True)
    thing_level = serializers.CharField(write_only=True, required=False)
    # user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Exercise
        fields = "__all__"
