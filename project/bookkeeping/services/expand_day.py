from datetime import datetime
from typing import Dict

from django.db.models import F
from django.utils.translation import gettext as _

from ...expenses.models import Expense


class ExpandDayService:
    def __init__(self, date: str):
        self._parse_date(date)

    def _parse_date(self, date: str) -> None:
        try:
            self._year = int(date[:4])
            self._month = int(date[4:6])
            self._day = int(date[6:8])
            self._date = datetime(self._year, self._month, self._day)
        except ValueError:
            self._year, self._month, self._day = 1970, 1, 1

        self._date = datetime(self._year, self._month, self._day)

    def _get_expenses(self) -> Dict:
        return \
            Expense.objects \
            .items() \
            .filter(date=self._date) \
            .order_by('expense_type', F('expense_name').asc(), 'price')

    def context(self) -> Dict:
        return {
            'day': self._day,
            'object_list': self._get_expenses(),
            'notice': _('No records on day %(day)s') % ({'day': f'{self._date:%F}'}),
        }
