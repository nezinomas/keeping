from datetime import datetime
from typing import Dict

from django.db.models import F
from django.utils.translation import gettext as _

from ...expenses.models import Expense


class ExpandDayService:
    def __init__(self, date: str):
        self.date = self._parse_date(date)
        self.data = self._get_expenses()

    def _parse_date(self, date: str) -> None:
        try:
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])
            date = datetime(year, month, day)
        except ValueError:
            year, month, day = 1974, 1, 1

        return datetime(year, month, day)

    def _get_expenses(self) -> Dict:
        return \
            Expense.objects \
            .items() \
            .filter(date=self.date) \
            .order_by('expense_type', F('expense_name').asc(), 'price')

    def context(self) -> Dict:
        return {
            'day': self.date.day,
            'object_list': self.data,
            'notice': _('No records on day %(day)s') % ({'day': f'{self.date:%F}'}),
        }
