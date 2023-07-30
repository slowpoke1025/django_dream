from django.urls import path, include
from . import views

urlpatterns = [
    path("gears/", views.GearView.as_view()),
    path("things/", views.ThingView.as_view()),
    path("exercises/", views.ExerciseView.as_view({"get": "list", "post": "create"})),
]

urlpatterns += [
    path("history/<int:year>/<int:month>/", views.ExerciseMonthView.as_view()),
    path("history/<int:year>/<int:month>/<int:day>/", views.ExerciseDayView.as_view()),
]

urlpatterns += [
    path("task/", views.ExerciseWeekView.as_view()),
    path("gacha/", views.GachaAPIView.as_view()),
]

urlpatterns += [
    path("read/", views.readView.as_view()),
    path("mint/", views.mintView.as_view()),
]
# .list(), .retrieve(), .create(), .update(), .partial_update(), .destroy()
