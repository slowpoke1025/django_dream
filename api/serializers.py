from .models import Thing, Gear, Exercise
from rest_framework import serializers


class ThingSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Thing
        fields = "__all__"


class GearSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exp = serializers.FloatField(read_only=True)

    class Meta:
        model = Gear
        fields = "__all__"


class ExerciseSerializers(serializers.ModelSerializer):
    # user = serializers.ReadOnlyField(source="user.username")
    # user = serializers.SerializerMethodField()
    # def get_user(self, obj):
    #     return {"id": obj.user.id, "username": obj.user.username}
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Exercise
        fields = "__all__"
