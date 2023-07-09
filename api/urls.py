from django.urls import path, include
from . import views

# from rest_framework.authtoken.views import ObtainAuthToken

urlpatterns = [
    path("gears/", views.GearView.as_view({"get": "list", "post": "create"})),
    path("gears/<int:pk>", views.GearView.as_view({"get": "retrieve"})),
    path("things/", views.ThingView.as_view({"get": "list", "post": "create"})),
    path("things/<int:pk>", views.ThingView.as_view({"get": "retrieve"})),
    path("exercises/", views.ExerciseView.as_view({"get": "list", "post": "create"})),
    path("exercises/<int:pk>", views.ExerciseView.as_view({"get": "retrieve"})),
]


# .list(), .retrieve(), .create(), .update(), .partial_update(), .destroy()
