from functools import reduce
from operator import or_

from django.db import models
from django.db.models import Count, F, Max, Q
from django.db.models.functions import ExtractYear

from ..core.lib import utils


class QsMixin:
    def filter_by_year(self, year):
        return (
            self.filter(**{"date__year__gte": (year - 1), "date__year__lte": year})
            if year
            else self
        )

    def latest_have(self, field):
        qs = [
            *(
                self.related()
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
                "year", latest_check=F("date"), id=F(f"{field}__id"), have=F("price")
            )
            if items
            else None
        )


class AccountWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created_and_closed(self, year):
        return (
            self.filter(
                Q(account__closed__isnull=True)
                | Q(account__closed__gte=year) & Q(account__created__year__lte=year)
            )
            if year
            else self
        )

    def related(self):
        journal = utils.get_user().journal
        return self.select_related("account").filter(account__journal=journal)

    def have(self):
        return self.latest_have(field="account")


class SavingWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created_and_closed(self, year):
        return (
            self.filter(
                Q(saving_type__closed__isnull=True)
                | Q(saving_type__closed__gte=year)
                & Q(saving_type__created__year__lte=year)
            )
            if year
            else self
        )

    def related(self):
        journal = utils.get_user().journal
        return self.select_related("saving_type").filter(saving_type__journal=journal)

    def have(self):
        return self.latest_have(field="saving_type")


class PensionWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created(self, year):
        return self.filter(Q(pension_type__created__year__lte=year)) if year else self

    def related(self):
        journal = utils.get_user().journal
        return self.select_related("pension_type").filter(pension_type__journal=journal)

    def have(self):
        return self.latest_have(field="pension_type")
