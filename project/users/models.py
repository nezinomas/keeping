from django.urls import reverse_lazy
from django.contrib.auth.models import AbstractUser
from django.db import models

from ..journals.models import Journal
from . import managers


class User(AbstractUser):
    year = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    month = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='users'
    )
    drink_type = models.CharField(
        max_length=16,
        default='beer'
    )
    email = models.EmailField(unique=True)

    objects = managers.KeepingUserManager()

    def __str__(self):
        return str(self.username)

    def save(self, *args, **kwarg):
        # create a journal for the new user
        if not hasattr(self, 'journal'):
            jr = Journal.objects.create(title=f'{self.username} Journal')
            self.journal = jr
            self.is_superuser = True

        return super().save(*args, **kwarg)

    def get_delete_url(self):
        return reverse_lazy("users:settings_users_delete", kwargs={"pk": self.pk})
