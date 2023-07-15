from .models import User
from .permissions import IsUserOrAdmin
from .serializers import ProfileSerializers, UserSerializers

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        # password = request.data.get("password")
        # user = authenticate(username=username, password=password)
        user = authenticate(request, username=username)
        

        if user:
            login(request, user)
            return Response({"message": "Login successfully"}, status=200)
        else:
            return Response({"message": "Invalid credentials"}, status=401)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout successfully"}, status=200)


class UserView(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializers

    # def perform_create(self, serializer):
    #     password = make_password(serializer.validated_data["password"])
    #     serializer.save(password=password)

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        elif self.action == "retrieve":
            permission_classes = [IsUserOrAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    # def perform_create(self, serializer):
    #     data = serializer.validated_data
    #     user = User.objects.create_user(
    #         username=data["username"], password=data["password"]
    #     )
    #     # serializer.save() # (user=user)


class ProfileView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializers
    permission_classes = [IsUserOrAdmin]
