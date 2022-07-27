import contextlib
from datetime import datetime
from typing import Dict, List

from django.db.models.query import QuerySet

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


class SummarySavingsService():
    def __init__(self):
        self._saving_data = self._get_saving_data()
        self._pension_data = self._get_pension_data()

    @property
    def records(self):
        return \
            self._saving_data.count() + \
            self._pension_data.count()

    @property
    def funds(self):
        return self._saving_data.filter(type='funds')

    @property
    def shares(self):
        return self._saving_data.filter(type='shares')

    @property
    def pensions2(self):
        return self._pension_data

    @property
    def pensions3(self):
        return self._saving_data.filter(type='pensions')

    def make_chart_data(self, *attr_names: str) -> List[Dict]:
        '''
        attr_names
        available: funds, shares, pensions2, pensions3
        '''
        data = []

        for attr in attr_names:
            with contextlib.suppress(AttributeError):
                data.append(getattr(self, attr))

        return __class__.chart_data(*data)

    def _get_saving_data(self):
        return SavingBalance.objects.sum_by_type()

    def _get_pension_data(self):
        return PensionBalance.objects.sum_by_year()

    @staticmethod
    def chart_data(*args):
        items = {
            'categories': [],
            'invested': [],
            'profit': [],
            'total': [],
            'max': 0
        }

        for arr in args:
            if isinstance(arr, QuerySet):
                arr = list(arr)

            if not arr or not isinstance(arr, list):
                continue

            cnt = len(arr)
            for i in range(cnt):
                _year = arr[i]['year']
                _invested = arr[i]['invested']
                _profit = arr[i]['profit']
                _total_sum = _invested + _profit

                if _year > datetime.now().year:
                    continue

                if _invested or _profit:
                    if _year not in items['categories']:
                        items['categories'].append(_year)
                        items['invested'].append(_invested)
                        items['profit'].append(_profit)
                        items['total'].append(_total_sum)
                    else:
                        ix = items['categories'].index(_year)  # category index
                        items['invested'][ix] += _invested
                        items['profit'][ix] += _profit
                        items['total'][ix] += _total_sum

        # max value
        if items['profit'] or items['invested']:
            items['max'] = (max(items['profit']) + max(items['invested']))

        return items
