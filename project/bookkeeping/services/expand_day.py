from datetime import date

from django.db.models import F
from django.utils.translation import gettext as _

from ...expenses.models import Expense


class ExpandDayService:
    def __init__(self, date: date):
        self.date = date
        self.data = self._get_expenses()

    def _get_expenses(self) -> list[dict]:
        return (
            Expense.objects.items()
            .filter(date=self.date)
            .order_by("expense_type", F("expense_name").asc(), "price")
        )

    def context(self) -> dict:
        return {
            "day": self.date.day,
            "object_list": self.data,
            "notice": _("No records on day %(day)s") % ({"day": f"{self.date:%F}"}),
        }
