from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from ...savings.factories import SavingBalance, SavingBalanceFactory
from .. import views
from ..lib import summary_view_helper as Helper

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                            Summary View
# ---------------------------------------------------------------------------------------
def test_func():
    view = resolve('/summary/')

    assert views.Summary == view.func.view_class


def test_200(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_salary_avg(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_data_avg'] == [1.0, 10.0]


@freeze_time('1999-01-01')
def test_salary_years(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_balance_years(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_incomes_avg(client_logged):
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Kita')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=10.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=2.0,
        income_type=IncomeTypeFactory(title='Kt')
    )

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_income_avg'] == [2.0, 12.0]


def test_no_data(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.context['records'] == 0
    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


def test_one_year_data(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.context['records'] == 1
    assert 'Trūksta duomenų. Reikia bent dviejų metų duomenų.' in actual


def test_view_context(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert 'records' in actual
    assert 'balance_categories' in actual
    assert 'balance_income_data' in actual
    assert 'balance_income_avg' in actual
    assert 'balance_expense_data' in actual
    assert 'salary_categories' in actual
    assert 'salary_data_avg' in actual


@freeze_time('1999-1-1')
def test_view_only_incomes(client_logged):
    IncomeFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_view_only_expenses(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_view_incomes_and_expenses(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['records'] == 1


@freeze_time('1999-1-1')
def test_chart_categories_years(client_logged):
    IncomeFactory()
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]
    assert actual['salary_categories'] == [1999]


@freeze_time('1999-1-1')
def test_chart_balance_categories_only_incomes(client_logged):
    IncomeFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]\


@freeze_time('1999-1-1')
def test_chart_balance_categories_only_expenses(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)
    actual = response.context

    assert actual['balance_categories'] == [1999]


# ---------------------------------------------------------------------------------------
#                                                                          Summary Helper
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


def test_helper_chart_data_1(_a):
    actual = Helper.chart_data(_a)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


@freeze_time('2000-1-1')
def test_helper_chart_data_2(_a):
    actual = Helper.chart_data(_a)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [1.0]
    assert actual['profit'] == [0.1]
    assert actual['total'] == [1.1]


def test_helper_chart_data_3(_a, _b):
    actual = Helper.chart_data(_a, _b)

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [5.0, 7.0]
    assert actual['profit'] == [0.5, 0.7]
    assert actual['total'] == [5.5, 7.7]


def test_helper_chart_data_5(_a):
    actual = Helper.chart_data(_a, [])

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


def test_helper_chart_data_6():
    actual = Helper.chart_data([])

    assert not actual['categories']
    assert not actual['invested']
    assert not actual['profit']
    assert not actual['total']


def test_helper_chart_data_7():
    actual = Helper.chart_data('x')

    assert not actual['categories']
    assert not actual['invested']
    assert not actual['profit']
    assert not actual['total']


@freeze_time('2000-1-1')
def test_helper_chart_data_4(_a, _b):
    actual = Helper.chart_data(_a, _b)

    assert actual['categories'] == [2000]
    assert actual['invested'] == [5.0]
    assert actual['profit'] == [0.5]
    assert actual['total'] == [5.5]


def test_helper_chart_data_max_value(_a, _b):
    actual = Helper.chart_data(_a, _b)

    assert actual['max'] == 7.7


def test_helper_chart_data_max_value_empty():
    actual = Helper.chart_data([])

    assert actual['max'] == 0


@pytest.mark.django_db
def test_helper_chart_data_db1():
    SavingBalanceFactory(year=1999, incomes=0, profit_incomes_sum=0)
    SavingBalanceFactory(year=2000, incomes=1, profit_incomes_sum=0.1)
    SavingBalanceFactory(year=2001, incomes=2, profit_incomes_sum=0.2)

    qs = SavingBalance.objects.sum_by_type()
    actual = Helper.chart_data(qs.filter(type='funds'))

    assert actual['categories'] == [2000, 2001]
    assert actual['invested'] == [1.0, 2.0]
    assert actual['profit'] == [0.1, 0.2]
    assert actual['total'] == [1.1, 2.2]


def test_helper_compare_categories():
    obj = Helper.ExpenseCompareHelper(years=[1, 2])

    actual = obj.categories

    assert actual == [1, 2]


def test_helper_compare_serries_data_types(types):
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


def test_helper_compare_serries_data_types_year_out_of_range(types):
    types.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_helper_compare_serries_data_types_no_data():
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002]
    )

    actual = obj.serries_data

    assert actual == []


def test_helper_compare_serries_data_names(names):
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


def test_helper_compare_serries_data_names_year_out_of_range(names):
    names.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_helper_compare_serries_data_full(types, names):
    obj = Helper.ExpenseCompareHelper(
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


def test_helper_compare_serries_data_remove_empty_columns():
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

    obj = Helper.ExpenseCompareHelper(
        years=[1, 2, 3, 4],
        types=types,
        remove_empty_columns=True
    )

    assert obj.categories == [1, 3]
    assert obj.serries_data == [
        {'name': 'X', 'data': [1.0, 3.0]},
        {'name': 'Y', 'data': [2.0, 4.0]},
    ]


def test_helper_compare_serries_data_remove_empty_columns_no_data():
    obj = Helper.ExpenseCompareHelper(
        years=[1, 2],
        remove_empty_columns=True
    )

    assert obj.categories == [1, 2]
    assert obj.serries_data == []


def test_helper_compare_serries_data_remove_empty_columns_no_data_all():
    obj = Helper.ExpenseCompareHelper(
        years=[],
        remove_empty_columns=True
    )

    assert obj.categories == []
    assert obj.serries_data == []


def test_helper_compare_serries_total_column(types):
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total_col
    expect = {'X': 20.0, 'Y': 14.0}

    assert actual == expect


def test_helper_compare_serries_total_row(types):
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total_row
    expect = [7.0, 12.0, 15.0]

    assert actual == expect


def test_helper_compare_serries_total(types):
    obj = Helper.ExpenseCompareHelper(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total

    assert actual == 34.0
