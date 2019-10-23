from datetime import datetime as dt
from decimal import Decimal

import mock
import pytest
import pytz

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...savings.factories import SavingTypeFactory
from .. import factories, models

pytestmark = pytest.mark.django_db


def test_account_worth_latest_values(accounts_worth):
    actual = list(models.AccountWorth.objects.items())

    expect = [
        {'title': 'Account1', 'have': 3.25},
        {'title': 'Account2', 'have': 8.0},
    ]

    assert_(expect, actual)


def test_account_worth_queries(django_assert_num_queries, accounts_worth):
    with django_assert_num_queries(1) as captured:
        list(models.AccountWorth.objects.items())


def test_saving_worth_latest_values(savings_worth):
    actual = list(models.SavingWorth.objects.items())

    expect = [
        {'title': 'Saving1', 'have': 0.15},
        {'title': 'Saving2', 'have': 6.15},
    ]

    assert_(expect, actual)


def test_saving_worth_queries(django_assert_num_queries, savings_worth):
    with django_assert_num_queries(1) as captured:
        list(models.SavingWorth.objects.items())


def test_saving_worth_str():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, 2, 3, 4, tzinfo=pytz.utc)

        model = factories.SavingWorthFactory()

    assert '1999-01-01 02:03 - Savings' == str(model)


def test_account_worth_str():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, 2, 3, 4, tzinfo=pytz.utc)

        model = factories.AccountWorthFactory()

    assert '1999-01-01 02:03 - Account1' == str(model)


def test_account_balance_queries(django_assert_num_queries):
    a1 = AccountFactory(title='a1')
    a2 = AccountFactory(title='a2')

    AccountBalanceFactory(account=a1)
    AccountBalanceFactory(account=a2)

    with django_assert_num_queries(1) as captured:
        list(AccountBalance.objects.all())
