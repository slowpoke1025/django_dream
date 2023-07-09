# from django.shortcuts import render
from .models import Thing, Gear, Exercise
from accounts.permissions import IsUserOrAdmin
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .serializers import (
    GearSerializers,
    ThingSerializers,
    ExerciseSerializers,
)


class ThingView(ModelViewSet):
    queryset = Thing.objects.all()
    serializer_class = ThingSerializers
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GearView(ModelViewSet):
    queryset = Gear.objects.all()
    serializer_class = GearSerializers
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseView(ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializers
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):  #
        data = serializer.validated_data
        gear = data.get("gear")
        accuracy = data.get("accuracy")  # or from server

        if gear.user != self.request.user:
            raise PermissionDenied("You are not allowed to modify this gear.")

        gear.exp += accuracy  # calculate exp with exercise...
        gear.save()

        serializer.save(user=self.request.user)

        # return Response(serializer.data, status=201) # customize response
