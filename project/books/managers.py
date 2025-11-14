from django.db import models

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class BooksQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("user").filter(user=user)


class BookTargetQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("user").filter(user=user)
