import json
from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from mock import Mock, patch

from ...core.tests.utils import setup_view
from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import (PensionBalance, PensionFactory,
                                   PensionTypeFactory)
from ...savings.factories import (SavingBalance, SavingFactory,
                                  SavingTypeFactory)
from ..lib import views_helpers as T
from ..views import Summary

pytestmark = pytest.mark.django_db


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


def test_add_latest_check_key_date_found():
    model = Mock()
    model.objects.items.return_value = [{'title': 'x', 'latest_check': 'a'}]

    actual = [{'title': 'x'}]

    T.add_latest_check_key(model, actual,666)

    assert actual == [{'title': 'x', 'latest_check': 'a'}]


def test_add_latest_check_key_date_not_found():
    model = Mock()
    model.objects.items.return_value = [{'title': 'z', 'latest_check': 'a'}]

    actual = [{'title': 'x'}]

    T.add_latest_check_key(model, actual, 666)

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
