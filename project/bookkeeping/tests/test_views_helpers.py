from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from mock import Mock, patch

from ...pensions.factories import (PensionBalance, PensionFactory,
                                   PensionTypeFactory)
from ...savings.factories import (SavingBalance, SavingFactory,
                                  SavingTypeFactory)
from ..lib import views_helpers as T


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects.items')
def test_expenses_types_no_args(qs):
    qs.return_value.values_list.return_value = ['T']

    actual = T.expense_types()

    assert ['T'] == actual


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects.items')
def test_expenses_types(qs):
    qs.return_value.values_list.return_value = ['T']

    actual = T.expense_types('A')

    assert ['A', 'T'] == actual


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects.items')
def test_expenses_types_args_as_list(qs):
    qs.return_value.values_list.return_value = ['T']

    actual = T.expense_types(*['X', 'A'])

    assert ['A', 'T', 'X'] == actual


def test_split_funds():
    lst = [{'title': 'AAA LX'}, {'title': 'INVL'}]

    a1, a2 = T.split_funds(lst, 'lx')

    assert a1[0]['title'] == 'AAA LX'
    assert a2[0]['title'] == 'INVL'


@pytest.fixture
def _income():
    return [
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(1)},
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(4)},
        {'date': date(1999, 6, 1), 'title': 'B', 'sum': Decimal(2)},
    ]


def test_sum_detailed_rows(_income):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5)},
        {'date': date(1999, 6, 1), 'sum': Decimal(2)},
    ]
    actual = T.sum_detailed(_income, 'date', ['sum'])

    assert expect == actual


def test_sum_detailed_columns(_income):
    expect = [
        {'title': 'A', 'sum': Decimal(5)},
        {'title': 'B', 'sum': Decimal(2)},
    ]

    actual = T.sum_detailed(_income, 'title', ['sum'])

    assert expect == actual


def test_percentage_from_incomes():
    actual = T.percentage_from_incomes(10, 1.5)

    assert actual == 15


def test_percentage_from_incomes_saving_none():
    actual = T.percentage_from_incomes(10, None)

    assert not actual


def test_add_latest_check_key_date_found():
    model = Mock()
    model.objects.items.return_value = [{'title': 'x', 'latest_check': 'a'}]

    actual = [{'title': 'x'}]

    T.add_latest_check_key(model, actual)

    assert actual == [{'title': 'x', 'latest_check': 'a'}]


def test_add_latest_check_key_date_not_found():
    model = Mock()
    model.objects.items.return_value = [{'title': 'z', 'latest_check': 'a'}]

    actual = [{'title': 'x'}]

    T.add_latest_check_key(model, actual)

    assert actual == [{'title': 'x', 'latest_check': None}]


@freeze_time('2000-2-5')
def test_average_current_year():
    qs = [{'year': 2000, 'sum': Decimal('12')}]

    actual = T.average(qs)

    assert actual == [6.0]


@freeze_time('2001-2-5')
def test_average_past_year():
    qs = [{'year': 2000, 'sum': Decimal('12')}]

    actual = T.average(qs)

    assert actual == [1.0]


@freeze_time('2000-2-5')
def test_average():
    qs = [
        {'year': 1999, 'sum': Decimal('12')},
        {'year': 2000, 'sum': Decimal('12')}
    ]

    actual = T.average(qs)

    assert actual == [1.0, 6.0]


# ---------------------------------------------------------------------------------------
#                                                                              No Incomes
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _expenses():
    arr = [
        {'sum': Decimal(1.00), 'title': 'X'},
        {'sum': Decimal(2.60), 'title': 'Y'},
        {'sum': Decimal(3.00), 'title': 'Z'},
        # --------------------------------------------------------------
        {'sum': Decimal(4.00), 'title': 'X'},
        {'sum': Decimal(5.60), 'title': 'Y'},
        {'sum': Decimal(6.00), 'title': 'Z'},
    ]
    return arr


@pytest.fixture
def _savings():
    arr = {'sum': Decimal(4.00)}
    return arr


@pytest.fixture
def _not_use():
    return ['Z']


@freeze_time('2020-07-07')
def test_no_incomes_data(_not_use, _expenses, _savings):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=_not_use, expenses=_expenses, savings=_savings)

    assert avg_expenses == pytest.approx(4.37, rel=1e-2)
    assert cut_sum == pytest.approx(2.17, rel=1e-2)


@freeze_time('2020-07-07')
def test_no_incomes_data_not_use_empty(_expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=[], expenses=_expenses)

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == 0.0


@freeze_time('2020-07-07')
def test_no_incomes_data_no_savings(_not_use, _expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=_not_use, expenses=_expenses)

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == pytest.approx(1.5, rel=1e-2)


@freeze_time('2020-07-07')
def test_no_incomes_data_savings_none(_not_use, _expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=_not_use, expenses=_expenses, savings={'sum': None})

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == pytest.approx(1.5, rel=1e-2)


# ---------------------------------------------------------------------------------------
#                                                                            Index Helper
# ---------------------------------------------------------------------------------------
@pytest.mark.django_db
def test_render_savings_no_data(rf):
    actual = T.IndexHelper(rf, 1999).render_savings()
    assert actual == ''


@pytest.mark.django_db
def test_render_savings_with_data(rf):
    SavingFactory()
    SavingFactory(saving_type=SavingTypeFactory(title='xxx'))
    actual = T.IndexHelper(rf, 1999).render_savings()

    assert '288,90' in actual # total invested sum


@pytest.mark.django_db
def test_render_savings_balances_no_generated(rf):
    SavingFactory()
    SavingBalance.objects.all().delete()
    actual = T.IndexHelper(rf, 1999).render_savings()

    assert actual == ''


@pytest.mark.django_db
def test_render_pensions_no_data(rf):
    actual = T.IndexHelper(rf, 1999).render_pensions()
    assert actual == ''


@pytest.mark.django_db
def test_render_pensions_with_data(rf):
    PensionFactory()
    PensionFactory(pension_type=PensionTypeFactory(title='xxx'))
    actual = T.IndexHelper(rf, 1999).render_pensions()

    assert '197,98' in actual # total invested sum


@pytest.mark.django_db
def test_render_pensions_balances_no_generated(rf):
    PensionFactory()
    PensionBalance.objects.all().delete()
    actual = T.IndexHelper(rf, 1999).render_savings()

    assert actual == ''
