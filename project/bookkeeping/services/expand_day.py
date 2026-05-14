from datetime import date

from django.db.models import F
from django.utils.translation import gettext as _

from ...core.lib.utils import add_fast_urls, get_action_buttons_html
from ...expenses.apps import App_name as Expenses_app_name
from ...expenses.services.model_services import ExpenseModelService
from ...users.models import User


class ExpandDayService:
    def __init__(self, user: User, date: date):
        self.user = user
        self.date = date
        self.data = self._get_expenses()

    def _get_expenses(self) -> list[dict]:
        service = ExpenseModelService(self.user)
        qs = (
            service.items()
            .filter(date=self.date)
            .order_by("expense_type", F("expense_name").asc(), "price")
        )

        data = service.expenses_list(qs)

        return add_fast_urls(data=data, app_name=Expenses_app_name)

    def context(self) -> dict:
        return {
            "day": self.date.day,
            "object_list": self.data,
            "notice": _("No records on day %(day)s") % ({"day": f"{self.date:%F}"}),
        } | get_action_buttons_html()
