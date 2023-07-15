from django.contrib.auth.backends import ModelBackend
from .models import User




class UserAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# class AdminAuthBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             user = Admin.objects.get(username=username)
#             if user.check_password(password):
#                 return user
#         except Admin.DoesNotExist:
#             return None

#     def get_user(self, user_id):
#         try:
#             return Admin.objects.get(pk=user_id)
#         except Admin.DoesNotExist:
#             return None
