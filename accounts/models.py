from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model, set as AUTH_USER_MODEL from project start.
    Login still uses username (Django's default) — email is just
    guaranteed unique so it can double as a contact/notification address.
    """
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
