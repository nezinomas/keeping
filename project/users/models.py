from django.contrib.auth.models import AbstractUser
from django.db import models

from ..drinks.lib.drink_types import DrinkType
from ..journals.models import Journal


class User(AbstractUser):
    year = models.PositiveIntegerField(null=True, blank=True)
    month = models.PositiveIntegerField(null=True, blank=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="users")
    drink_type = models.CharField(
        max_length=16,
        choices=DrinkType.choices,
        default=DrinkType.BEER,
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return str(self.username)

    def selected_year(self) -> int:
        # NULL until the first login sets it
        if self.year is None:
            raise ValueError(f"{self} has no year")
        return self.year

    def save(self, *args, **kwarg):
        # create a journal for the new user
        if not hasattr(self, "journal"):
            jr = Journal.objects.create(title=Journal.title_for(self.username))
            self.journal = jr
            self.is_superuser = True

        return super().save(*args, **kwarg)
