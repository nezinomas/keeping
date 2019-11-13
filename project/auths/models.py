from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    year = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    month = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return str(self.username)
