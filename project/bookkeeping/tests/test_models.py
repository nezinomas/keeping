from datetime import datetime as dt
from decimal import Decimal

import mock
import pytest
import pytz

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...users.factories import UserFactory
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...pensions.factories import PensionTypeFactory
from ...pensions.models import PensionBalance
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingBalance
from ..factories import (AccountWorthFactory, PensionWorthFactory,
                         SavingWorthFactory)
from ..models import AccountWorth, PensionWorth, SavingWorth

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                 AccountWorth
# ---------------------------------------------------------------------------
def test_account_worth_str():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, 2, 3, 4, tzinfo=pytz.utc)

        model = AccountWorthFactory()

    assert str(model) == '1999-01-01 02:03 - Account1'


def test_account_worth_related(get_user):
    u = UserFactory(username='XXX')
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2', user=u)

    AccountWorthFactory(account=a1)
    AccountWorthFactory(account=a2)

    actual = AccountWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].account) == 'A1'
    assert actual[0].account.user.username == 'bob'


def test_account_worth_latest_values(get_user, accounts_worth):
    actual = list(AccountWorth.objects.items())

    expect = [
        {'title': 'Account1', 'have': 3.25},
        {'title': 'Account2', 'have': 8.0},
    ]

    assert_(expect, actual)


def test_account_worth_queries(get_user, accounts_worth,
                               django_assert_num_queries):
    with django_assert_num_queries(1):
        list(AccountWorth.objects.items())


def test_account_worth_post_save(get_user):
    a1 = AccountFactory(title='a1')

    AccountWorth(price=Decimal(1), account=a1).save()

    actual = AccountBalance.objects.items(1999)

    assert actual.count() == 1


# ----------------------------------------------------------------------------
#                                                                  SavingWorth
# ----------------------------------------------------------------------------
def test_saving_worth_str():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, 2, 3, 4, tzinfo=pytz.utc)

        model = SavingWorthFactory()

    assert str(model) == '1999-01-01 02:03 - Savings'


def test_saving_worth_related(get_user):
    u = UserFactory(username='XXX')
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', user=u)

    SavingWorthFactory(saving_type=s1)
    SavingWorthFactory(saving_type=s2)

    actual = SavingWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'S1'
    assert actual[0].saving_type.user.username == 'bob'


def test_saving_worth_latest_values(get_user, savings_worth):
    actual = list(SavingWorth.objects.items())

    expect = [
        {'title': 'Saving1', 'have': 0.15},
        {'title': 'Saving2', 'have': 6.15},
    ]

    assert_(expect, actual)


def test_saving_worth_queries(get_user, savings_worth,
                              django_assert_num_queries):
    with django_assert_num_queries(1):
        list(SavingWorth.objects.items())


def test_saving_worth_post_save(get_user):
    s1 = SavingTypeFactory(title='s1')

    SavingWorth(price=Decimal(1), saving_type=s1).save()

    actual = SavingBalance.objects.items(1999)

    assert actual.count() == 1


# ----------------------------------------------------------------------------
#                                                                 PensionWorth
# ----------------------------------------------------------------------------
def test_pension_worth_str():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = dt(1999, 1, 1, 2, 3, 4, tzinfo=pytz.utc)

        model = PensionWorthFactory()

    assert str(model) == '1999-01-01 02:03 - PensionType'


def test_pension_worth_related(get_user):
    u = UserFactory(username='XXX')
    p1 = PensionTypeFactory(title='P1')
    p2 = PensionTypeFactory(title='P2', user=u)

    PensionWorthFactory(pension_type=p1)
    PensionWorthFactory(pension_type=p2)

    actual = PensionWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].pension_type) == 'P1'
    assert actual[0].pension_type.user.username == 'bob'


def test_pension_worth_latest_values(get_user, pensions_worth):
    actual = list(PensionWorth.objects.items())

    expect = [
        {'title': 'PensionType', 'have': 2.15},
    ]

    assert_(expect, actual)


def test_pension_worth_queries(get_user, pensions_worth,
                               django_assert_num_queries,):
    with django_assert_num_queries(1):
        list(PensionWorth.objects.items())


def test_pension_worth_post_save(get_user):
    p1 = PensionTypeFactory(title='P1')

    PensionWorth(price=Decimal(1), pension_type=p1).save()

    actual = PensionBalance.objects.items(1999)

    assert actual.count() == 1
