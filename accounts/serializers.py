from .models import User
from rest_framework import serializers


class UserSerializers(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    last_login = serializers.ReadOnlyField()
    is_superuser = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = "__all__"


class ProfileSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "gender", "weight", "height", "birth")
