from .models import User
from rest_framework import serializers


class UserSerializers(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)
    last_login = serializers.ReadOnlyField()
    is_superuser = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value
        
    # def validate(self, data):
    #     email = data.get('email')
    #     if email and User.objects.filter(email=email).exists():
    #         raise serializers.ValidationError("Email is already in use.")
    #     return data
    
    class Meta:
        model = User
        fields = "__all__"


class ProfileSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "gender", "weight", "height", "birth", "email")
