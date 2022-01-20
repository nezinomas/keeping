from datetime import date
from decimal import Decimal
import pytest
from freezegun import freeze_time

from ...savings.factories import SavingBalance, SavingBalanceFactory
from ..lib import summary_view_helper as H


# ---------------------------------------------------------------------------------------
#                                                                               fixtures
# ---------------------------------------------------------------------------------------
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


@pytest.fixture
def types():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'X'},
    ]


@pytest.fixture
def names():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'A', 'root': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'B', 'root': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'B', 'root': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'A', 'root': 'X'},
    ]


# ---------------------------------------------------------------------------------------
#                                                                               fixtures
# ---------------------------------------------------------------------------------------


def test_chart_data_1(_a):
    actual = H.chart_data(_a)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


@freeze_time('2000-1-1')
def test_chart_data_2(_a):
    actual = H.chart_data(_a)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [1.0]
    assert actual['profit'] == [0.1]
    assert actual['total'] == [1.1]


def test_chart_data_3(_a, _b):
    actual = H.chart_data(_a, _b)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [5.0, 7.0]
    assert actual['profit'] == [0.5, 0.7]
    assert actual['total'] == [5.5, 7.7]


def test_chart_data_5(_a):
    actual = H.chart_data(_a, [])

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


def test_chart_data_6():
    actual = H.chart_data([])

    assert actual['categories'] == []
    assert actual['invested'] == []
    assert actual['profit'] == []
    assert actual['total'] == []


def test_chart_data_7():
    actual = H.chart_data('x')

    assert actual['categories'] == []
    assert actual['invested'] == []
    assert actual['profit'] == []
    assert actual['total'] == []


@freeze_time('2000-1-1')
def test_chart_data_4(_a, _b):
    actual = H.chart_data(_a, _b)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [5.0]
    assert actual['profit'] == [0.5]
    assert actual['total'] == [5.5]


def test_chart_data_max_value(_a, _b):
    actual = H.chart_data(_a, _b)

    assert actual['max'] == 7.7


def test_chart_data_max_value_empty():
    actual = H.chart_data([])

    assert actual['max'] == 0


@pytest.mark.django_db
def test_chart_data_db1():
    SavingBalanceFactory(year=1999, incomes=0, profit_incomes_sum=0)
    SavingBalanceFactory(year=2000, incomes=1, profit_incomes_sum=0.1)
    SavingBalanceFactory(year=2001, incomes=2, profit_incomes_sum=0.2)

    qs = SavingBalance.objects.sum_by_type()
    actual = H.chart_data(qs.filter(type='funds'))

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


def test_make_form_data_dict(rf):
    form_data = '[{"name": "csrf", "value":"xxx"},{"name":"types","value":"1"},{"name":"types","value":"6:6"}]'

    actual = H.make_form_data_dict(form_data)

    assert actual['types'] == [1]
    assert actual['names'] == '6'
    assert actual['csrf'] == 'xxx'


def test_make_form_data_dict_extended(rf):
    form_data = '[{"name":"types","value":"1"},{"name":"types","value":"6:6"},{"name":"types","value":"2"},{"name":"types","value":"1:7"}]'

    actual = H.make_form_data_dict(form_data)

    assert actual['types'] == [1, 2]
    assert actual['names'] == '6,7'


def test_compare_categories():
    obj = H.ExpenseCompareHelper(years=[1, 2])

    actual = obj.categories

    assert actual == [1, 2]


def test_compare_serries_data_types(types):
    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect

def test_compare_serries_data_types_year_out_of_range(types):
    types.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_compare_serries_data_types_no_data():
    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002]
    )

    actual = obj.serries_data

    assert actual == []


def test_compare_serries_data_names(names):
    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


def test_compare_serries_data_names_year_out_of_range(names):
    names.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_compare_serries_data_full(types, names):
    obj = H.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types,
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_compare_serries_data_remove_empty_columns():
    types = [
        {'year': 1, 'sum': Decimal('1'), 'title': 'X'},
        {'year': 1, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2, 'sum': Decimal('0'), 'title': 'X'},
        {'year': 2, 'sum': Decimal('0'), 'title': 'Y'},
        {'year': 3, 'sum': Decimal('3'), 'title': 'X'},
        {'year': 3, 'sum': Decimal('4'), 'title': 'Y'},
        {'year': 4, 'sum': Decimal('0'), 'title': 'X'},
        {'year': 4, 'sum': Decimal('0'), 'title': 'Y'},
    ]

    obj = H.ExpenseCompareHelper(
        years=[1, 2, 3, 4],
        types=types,
        remove_empty_columns = True
    )

    assert obj.categories == [1, 3]
    assert obj.serries_data == [
        {'name': 'X', 'data': [1.0, 3.0]},
        {'name': 'Y', 'data': [2.0, 4.0]},
    ]
