from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models


class CountModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return (
            models.Count.objects.select_related("user")
            .filter(user=self.user)
            .order_by("-date")
        )

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

        return self.year_sum(
            qs, year=year, sum_annotation="qty", sum_column="quantity"
        ).order_by("date")

    def sum_by_day(self, year, count_type=None, month=None) -> list:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.objects

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return self.day_sum(
            qs, year=year, month=month, sum_annotation="qty", sum_column="quantity"
        ).order_by("date")


class CountTypeModelService(BaseModelService):
    def get_queryset(self):
        return models.CountType.objects.select_related("user").filter(user=self.user)

    def year(self, year):
        raise NotImplementedError(
            "CountTypeModelService.year is not implemented. Use items() instead."
        )

    def items(self):
        return self.objects
