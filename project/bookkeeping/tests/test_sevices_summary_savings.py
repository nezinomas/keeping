import pytest
from freezegun import freeze_time

from ...savings.factories import SavingBalance, SavingBalanceFactory
from ..services.summary_savings import SummarySavingsService

pytestmark = pytest.mark.django_db


@pytest.fixture
def _a():
    return ([
        {'year': 1999, 'invested': 0.0, 'profit': 0.0},
        {'year': 2000, 'invested': 1.0, 'profit': 0.1},
        {'year': 2001, 'invested': 2.0, 'profit': 0.2},
    ])


@pytest.fixture
def _b():
    return ([
        {'year': 1999, 'invested': 0.0, 'profit': 0.0},
        {'year': 2000, 'invested': 4.0, 'profit': 0.4},
        {'year': 2001, 'invested': 5.0, 'profit': 0.5},
    ])


def test_chart_data_1(_a):
    actual = SummarySavingsService.chart_data(_a)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


@freeze_time('2000-1-1')
def test_chart_data_2(_a):
    actual = SummarySavingsService.chart_data(_a)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [1.0]
    assert actual['profit'] == [0.1]
    assert actual['total'] == [1.1]


def test_chart_data_3(_a, _b):
    actual = SummarySavingsService.chart_data(_a, _b)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [5.0, 7.0]
    assert actual['profit'] == [0.5, 0.7]
    assert actual['total'] == [5.5, 7.7]


def test_chart_data_5(_a):
    actual = SummarySavingsService.chart_data(_a, [])

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


def test_chart_data_6():
    actual = SummarySavingsService.chart_data([])

    assert not actual['categories']
    assert not actual['invested']
    assert not actual['profit']
    assert not actual['total']


@freeze_time('2000-1-1')
def test_chart_data_4(_a, _b):
    actual = SummarySavingsService.chart_data(_a, _b)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [5.0]
    assert actual['profit'] == [0.5]
    assert actual['total'] == [5.5]


def test_chart_data_max_value(_a, _b):
    actual = SummarySavingsService.chart_data(_a, _b)

    assert actual['max'] == 7.7


def test_chart_data_max_value_empty():
    actual = SummarySavingsService.chart_data([])

    assert actual['max'] == 0


@pytest.mark.django_db
def test_chart_data_db1():
    SavingBalanceFactory(year=1999, incomes=0, invested=0, profit_sum=0)
    SavingBalanceFactory(year=2000, incomes=1, invested=1, profit_sum=0.1)
    SavingBalanceFactory(year=2001, incomes=2, invested=2, profit_sum=0.2)

    qs = SavingBalance.objects.sum_by_type()

    actual = SummarySavingsService.chart_data(list(qs.filter(type='funds')))

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]
