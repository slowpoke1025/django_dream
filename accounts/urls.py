from django.urls import path, include
from . import views

# from rest_framework.authtoken.views import ObtainAuthToken


# authentication
urlpatterns = [
    # path("token/", ObtainAuthToken.as_view()),
    path("login/", views.LoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("register/", views.UserView.as_view({"post": "create"})),
]

# development only
urlpatterns += [
    path("users/", views.UserView.as_view({"get": "list"})),
    path("users/<int:pk>", views.UserView.as_view({"get": "retrieve"})),
]

# GET, PATCH, PUT user profile
urlpatterns += [
    path("users/<int:pk>/profile/", views.ProfileView.as_view()),
]
