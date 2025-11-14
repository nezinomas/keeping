from functools import reduce
from operator import or_

from django.db import models
from django.db.models import Count, F, Max, Q
from django.db.models.functions import ExtractYear

from ..users.models import User


class QsMixin:
    def latest_have(self, user: User, field: str):
        qs = [
            *(
                self.related(user)
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
            self.filter(reduce(or_, items))
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


class AccountWorthQuerySet(QsMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account").filter(account__journal=user.journal)

    def have(self, user: User):
        return self.latest_have(user, field="account")


class SavingWorthQuerySet(QsMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("saving_type").filter(
            saving_type__journal=user.journal
        )

    def have(self, user: User):
        return self.latest_have(user, field="saving_type")


class PensionWorthQuerySet(QsMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )

    def have(self, user: User):
        return self.latest_have(user, field="pension_type")
