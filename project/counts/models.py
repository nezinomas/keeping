from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse_lazy

from project.core.models import TitleAbstract

from ..users.models import User
from .managers import CountQuerySet, CountTypeQuerySet


class CountType(TitleAbstract):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CountTypeQuerySet.as_manager()

    class Meta:
        unique_together = ["user", "title"]
        ordering = ["title"]

    def __str__(self):
        return str(self.title)


class Count(models.Model):
    date = models.DateField()
    quantity = models.FloatField(validators=[MinValueValidator(0.1)])
    count_type = models.ForeignKey(
        CountType, on_delete=models.CASCADE, related_name="counts"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CountQuerySet.as_manager()

    def __str__(self):
        return f"{self.date}: {self.quantity}"

    class Meta:
        ordering = ["-date"]
        get_latest_by = ["date"]
