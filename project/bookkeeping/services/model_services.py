from functools import reduce
from operator import or_
from typing import cast

from django.db.models import Count, F, Max, Q, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth

from ...core.services.model_services import BaseModelService
from ...users.models import User
from .. import managers, models


class QsMixin:
    def year(self, year: int):
        raise NotImplementedError(
            "Method year is not implemented."
        )

    def items(self):
        raise NotImplementedError(
            "Method items is not implemented."
        )

    def latest_have(self, field: str):
        qs = [
            *(
                self.objects
                .annotate(year=ExtractYear(F("date")))
                .values("year", f"{field}_id")
                .annotate(latest_date=Max("date"))
                .order_by("year")
            )
        ]

        # items = [ <Q AND( ('date': datetime), ('field_id': int) )>, ... ]
        fld = f"{field}_id"
        items = [Q(date=x["latest_date"]) & Q(**{fld: x[fld]}) for x in qs]

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
            if items
            else None
        )


class AccountWorthModelService(QsMixin, BaseModelService[managers.AccountWorthQuerySet]):
    def __init__(self, user: User):
        super().__init__(user)

    def get_queryset(self):
        return cast(managers.AccountWorthQuerySet, models.AccountWorth.objects).related(
            self.user
        )

    def have(self):
        return self.latest_have(field="account")


class SavingWorthModelService(QsMixin, BaseModelService[managers.SavingWorthQuerySet]):
    def __init__(self, user: User):
        super().__init__(user)

    def get_queryset(self):
        return cast(managers.SavingWorthQuerySet, models.SavingWorth.objects).related(
            self.user
        )

    def have(self):
        return self.latest_have(field="saving_type")


class PensionWorthModelService(QsMixin, BaseModelService[managers.PensionWorthQuerySet]):
    def __init__(self, user: User):
        super().__init__(user)

    def get_queryset(self):
        return cast(managers.PensionWorthQuerySet, models.PensionWorth.objects).related(
            self.user
        )

    def have(self):
        return self.latest_have(field="pension_type")