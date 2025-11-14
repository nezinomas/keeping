from typing import cast

from ...users.models import User
from .. import managers, models


class CountModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(managers.CountQuerySet, models.Count.objects).related(user)

    def year(self, year, count_type=None):
        qs = self.objects

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return qs.filter(date__year=year)

    def items(self, count_type=None):
        qs = self.objects

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return qs

    def sum_by_year(self, year=None, count_type=None):
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.objects

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return qs.year_sum(
            year=year, sum_annotation="qty", sum_column="quantity"
        ).order_by("date")

    def sum_by_day(self, year, count_type=None, month=None) -> list:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.objects

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return qs.day_sum(
            year=year, month=month, sum_annotation="qty", sum_column="quantity"
        ).order_by("date")


class CountTypeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.CountTypeQuerySet, models.CountType.objects
        ).related(user)

    def items(self):
        return self.objects
