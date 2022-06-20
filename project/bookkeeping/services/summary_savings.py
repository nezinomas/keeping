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
        data = []

        for attr in attr_names:
            try:
                data.append(getattr(self, attr))
            except AttributeError:
                pass

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
            for i in range(0, cnt):
                _y = arr[i]['year']
                _i = arr[i]['invested']
                _p = arr[i]['profit']
                _t = _i + _p

                if _y > datetime.now().year:
                    continue

                if _i or _p:
                    if _y not in items['categories']:
                        items['categories'].append(_y)
                        items['invested'].append(_i)
                        items['profit'].append(_p)
                        items['total'].append(_t)
                    else:
                        ix = items['categories'].index(_y)  # category index
                        items['invested'][ix] += _i
                        items['profit'][ix] += _p
                        items['total'][ix] += _t

        # max value
        if items['profit'] or items['invested']:
            items['max'] = (max(items['profit']) + max(items['invested']))

        return items
