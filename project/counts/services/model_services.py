from typing import cast

from ...core.services.model_services import BaseModelService
from .. import managers, models


class CountModelService(BaseModelService[managers.CountQuerySet]):
    def get_queryset(self):
        return cast(managers.CountQuerySet, models.Count.objects).related(self.user)

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


class CountTypeModelService(BaseModelService[managers.CountTypeQuerySet]):
    def get_queryset(self):
        return cast(managers.CountTypeQuerySet, models.CountType.objects).related(
            self.user
        )

    def year(self, year):
        raise NotImplementedError(
            "CountTypeModelService.year is not implemented. Use items() instead."
        )

    def items(self):
        return self.objects
