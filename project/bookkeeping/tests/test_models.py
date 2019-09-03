from datetime import datetime as dt

import mock
import pytest
import pytz

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from .. import factories, models

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _account_worth():
    account = AccountFactory(title='A')

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1970, 1, 1, tzinfo=pytz.utc)
        factories.AccountWorthFactory(
            price=1.0,
            account=account
        )

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, tzinfo=pytz.utc)
        factories.AccountWorthFactory(
            price=2.0,
            account=account
        )


@pytest.fixture()
def _saving_worth():
    saving_type = SavingTypeFactory()

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1970, 1, 1, tzinfo=pytz.utc)
        factories.SavingWorthFactory(
            price=1.0,
            saving_type=saving_type
        )

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, tzinfo=pytz.utc)
        factories.SavingWorthFactory(
            price=2.0,
            saving_type=saving_type
        )


def test_account_worth_latest(_account_worth):
    actual = models.AccountWorth.objects.items()

    assert 1 == len(actual)
    assert 2.0 == actual[0].price


def test_account_worth_queries(django_assert_num_queries, _account_worth):
    with django_assert_num_queries(1) as captured:
        list(models.AccountWorth.objects.items())


def test_saving_worth_latest(_saving_worth):
    actual = models.SavingWorth.objects.items()

    assert 1 == len(actual)
    assert 2.0 == actual[0].price


def test_saving_worth_queries(django_assert_num_queries, _saving_worth):
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
