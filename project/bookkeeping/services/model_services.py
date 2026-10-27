from functools import reduce
from operator import or_

from django.db.models import Count, F, Max, Q
from django.db.models.functions import ExtractYear

from ...core.services.model_services import BaseModelService
from .. import models


class CommonMethodsMixin:
    def items(self):
        raise NotImplementedError("Method items is not implemented.")

    def latest_have(self, field: str):
        qs = [
            *(
                self.objects.annotate(year=ExtractYear(F("date")))
                .values("year", f"{field}_id")
                .annotate(latest_date=Max("date"))
                .order_by("year")
            )
        ]

        fld = f"{field}_id"
        items = [Q(date=x["latest_date"]) & Q(**{fld: x[fld]}) for x in qs]
        if not items:
            return []

        return (
            self.objects.filter(reduce(or_, items))
            .annotate(c=Count("id"))
            .values("c")
            .annotate(year=ExtractYear(F("date")))
            .values(
                "year",
                latest_check=F("date"),
                category_id=F(f"{field}__id"),
                have=F("price"),
            )
        )


class AccountWorthModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.AccountWorth.objects.select_related("account").filter(
            account__journal=self.user.journal
        )

    def have(self):
        return self.latest_have(field="account")


class SavingWorthModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.SavingWorth.objects.select_related("saving_type").filter(
            saving_type__journal=self.user.journal
        )

    def have(self):
        return self.latest_have(field="saving_type")


class PensionWorthModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.PensionWorth.objects.select_related("pension_type").filter(
            pension_type__journal=self.user.journal
        )

    def have(self):
        return self.latest_have(field="pension_type")
