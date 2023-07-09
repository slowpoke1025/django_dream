from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,
    # PermissionsMixin,
    # AbstractUser,
)
from .managers import CustomUserManager


GENDER = (
    ("Male", "MALE"),
    ("Female", "FEMALE"),
    ("Other", "OTHER"),
)


class User(AbstractBaseUser):  # ,PermissionsMixin
    # address = models.CharField(max_length=42, unique=True, editable=False) # in production

    # unique = False in production
    username = models.CharField(max_length=255, unique=True)

    weight = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(choices=GENDER, max_length=6, blank=True, null=True)
    birth = models.DateField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    # email = models.EmailField(max_length=255, unique=True)  # remove ?

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"  # switch to address in production
    objects = CustomUserManager()

    # blank=False does not automatically make a field required for superuser creation or other specific operations.
    # It only enforces that a value must be provided when creating a new instance of the model.
    REQUIRED_FIELDS = []

    def __str__(self):
        # return self.address
        return self.username

    # set to use admin site without inherit PermissionMixin
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    # set to use admin site without inherit PermissionMixin
    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        return self.is_superuser

    class Meta:
        managed = True
        db_table = "user"
