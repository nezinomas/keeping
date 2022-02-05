from datetime import datetime as dt
from decimal import Decimal

import mock
import pytest
import pytz
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...pensions.factories import PensionTypeFactory
from ...pensions.models import PensionBalance
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingBalance
from ..factories import (AccountWorthFactory, PensionWorthFactory,
                         SavingWorthFactory)
from ..models import AccountWorth, PensionWorth, SavingWorth

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                            AccountWorth
# ---------------------------------------------------------------------------------------
def test_account_worth_str():
    actual = AccountWorthFactory()

    assert str(actual) == '1999-01-01 02:03 - Account1'


def test_account_worth_related(second_user):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2', journal=second_user.journal)

    AccountWorthFactory(account=a1)
    AccountWorthFactory(account=a2)

    actual = AccountWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].account) == 'A1'
    assert actual[0].account.journal.users.first().username == 'bob'


def test_account_worth_latest_values(accounts_worth):
    actual = list(AccountWorth.objects.items())

    expect = [
        {'title': 'Account1', 'have': Decimal('3.25')},
        {'title': 'Account2', 'have': Decimal('8.00')},
    ]

    assert_(expect, actual)



def test_account_worth_queries(accounts_worth,
                               django_assert_num_queries):
    with django_assert_num_queries(2):
        list(AccountWorth.objects.items())


def test_account_worth_post_save():
    AccountWorthFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1


# ---------------------------------------------------------------------------------------
#                                                                  SavingWorth
# ---------------------------------------------------------------------------------------
def test_saving_worth_str():
    model = SavingWorthFactory()

    assert str(model) == '1999-01-01 02:03 - Savings'


def test_saving_worth_related(second_user):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', journal=second_user.journal)

    SavingWorthFactory(saving_type=s1)
    SavingWorthFactory(saving_type=s2)

    actual = SavingWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'S1'
    assert actual[0].saving_type.journal.users.first().username == 'bob'


def test_saving_worth_latest_values(savings_worth):
    actual = SavingWorth.objects.items()

    assert actual[0]['title'] ==  'Saving1'
    assert actual[0]['have'] == Decimal('0.15')
    assert actual[0]['latest_check'] == dt(1999, 1, 2, tzinfo = pytz.utc)

    assert actual[1]['title'] ==  'Saving2'
    assert actual[1]['have'] == Decimal('6.15')
    assert actual[1]['latest_check'] == dt(1999, 1, 1, tzinfo = pytz.utc)


def test_saving_worth_queries(savings_worth,
                              django_assert_num_queries):
    with django_assert_num_queries(2):
        list(SavingWorth.objects.items())


def test_saving_worth_post_save():
    SavingWorthFactory()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1


# ---------------------------------------------------------------------------------------
#                                                                 PensionWorth
# ---------------------------------------------------------------------------------------
def test_pension_worth_str():
    model = PensionWorthFactory()

    assert str(model) == '1999-01-01 02:03 - PensionType'


def test_pension_worth_related(second_user):
    p1 = PensionTypeFactory(title='P1')
    p2 = PensionTypeFactory(title='P2', journal=second_user.journal)

    PensionWorthFactory(pension_type=p1)
    PensionWorthFactory(pension_type=p2)

    actual = PensionWorth.objects.related()

    assert len(actual) == 1
    assert str(actual[0].pension_type) == 'P1'
    assert actual[0].pension_type.journal.users.first().username == 'bob'


def test_pension_worth_latest_values(pensions_worth):
    actual = list(PensionWorth.objects.items())

    expect = [
        {'title': 'PensionType', 'have': 2.15},
    ]

    assert_(expect, actual)


def test_pension_worth_queries(pensions_worth,
                               django_assert_num_queries,):
    with django_assert_num_queries(2):
        list(PensionWorth.objects.items())


def test_pension_worth_post_save():
    PensionWorthFactory()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
