import pytest
import time_machine

from ...savings.factories import SavingBalance, SavingBalanceFactory
from ..services.summary_savings import make_chart_data

pytestmark = pytest.mark.django_db


@pytest.fixture
def _a():
    return [
        {"year": 1999, "invested": 0, "profit": 0},
        {"year": 2000, "invested": 1, "profit": 1},
        {"year": 2001, "invested": 2, "profit": 2},
    ]


@pytest.fixture
def _b():
    return [
        {"year": 1999, "invested": 0, "profit": 0},
        {"year": 2000, "invested": 4, "profit": 4},
        {"year": 2001, "invested": 5, "profit": 5},
    ]


def test_chart_data_1(_a):
    actual = make_chart_data(_a)

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


@time_machine.travel("2000-1-1")
def test_chart_data_2(_a):
    actual = make_chart_data(_a)

    assert actual["categories"] == [2000]
    assert actual["invested"] == [1]
    assert actual["profit"] == [1]
    assert actual["total"] == [2]


def test_chart_data_3(_a, _b):
    actual = make_chart_data(_a, _b)

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [5, 7]
    assert actual["profit"] == [5, 7]
    assert actual["total"] == [10, 14]


def test_chart_data_5(_a):
    actual = make_chart_data(_a, [])

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


def test_chart_data_6():
    actual = make_chart_data([])

    assert not actual["categories"]
    assert not actual["invested"]
    assert not actual["profit"]
    assert not actual["total"]


@time_machine.travel("2000-1-1")
def test_chart_data_4(_a, _b):
    actual = make_chart_data(_a, _b)

    assert actual["categories"] == [2000]
    assert actual["invested"] == [5]
    assert actual["profit"] == [5]
    assert actual["total"] == [10]


def test_chart_data_max_value(_a, _b):
    actual = make_chart_data(_a, _b)

    assert actual["max"] == 14


def test_chart_data_max_value_empty():
    actual = make_chart_data([])

    assert actual["max"] == 0


@pytest.mark.django_db
def test_chart_data_db1():
    SavingBalanceFactory(year=1999, incomes=0, invested=0, profit_sum=0)
    SavingBalanceFactory(year=2000, incomes=1, invested=1, profit_sum=1)
    SavingBalanceFactory(year=2001, incomes=2, invested=2, profit_sum=2)

    qs = SavingBalance.objects.sum_by_type()

    actual = make_chart_data(list(qs.filter(type="funds")))

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]
