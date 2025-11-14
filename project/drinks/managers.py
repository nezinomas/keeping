from django.db.models import QuerySet

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class DrinkQuerySet(SumMixin, QuerySet):
    def related(self, user: User):
        return self.select_related("user").filter(user=user).order_by("-date")


class DrinkTargetQuerySet(SumMixin, QuerySet):
    def related(self, user: User):
        return self.select_related("user").filter(user=user)
