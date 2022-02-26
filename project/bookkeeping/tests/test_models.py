from datetime import datetime as dt
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
import pytz

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...pensions.factories import PensionBalanceFactory, PensionTypeFactory
from ...pensions.models import PensionBalance
from ...savings.factories import SavingBalanceFactory, SavingTypeFactory
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
    actual = AccountWorth.objects.items()

    assert actual[0]['title'] == 'Account1'
    assert actual[0]['have'] == Decimal('3.25')
    assert actual[0]['latest_check'].year == 1999
    assert actual[0]['latest_check'].month == 1
    assert actual[0]['latest_check'].day == 2

    assert actual[1]['title'] == 'Account2'
    assert actual[1]['have'] == Decimal('8.0')
    assert actual[1]['latest_check'].year == 1999
    assert actual[1]['latest_check'].month == 1
    assert actual[1]['latest_check'].day == 1


def test_account_worth_queries(accounts_worth,
                               django_assert_num_queries):
    with django_assert_num_queries(2):
        list(AccountWorth.objects.items())


def test_account_worth_post_save():
    AccountWorthFactory(date=dt(1999, 1, 1, tzinfo=ZoneInfo('UTC')))

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['incomes'] == 0.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 0.5
    assert actual[0]['delta'] == 0.5


def test_account_worth_post_save_new():
    AccountBalanceFactory()

    actual = AccountBalance.objects.first()
    assert actual.have == 0.2

    AccountWorthFactory(price=5)

    actual = AccountBalance.objects.first()
    assert actual.have == 5.0


def test_account_worth_have():
    AccountWorthFactory(date=dt(1970, 1, 1, tzinfo=ZoneInfo('UTC')), price=1)
    AccountWorthFactory(date=dt(1970, 12, 31, tzinfo=ZoneInfo('UTC')), price=2)
    AccountWorthFactory(date=dt(2000, 1, 1, tzinfo=ZoneInfo('UTC')), price=3)
    AccountWorthFactory(date=dt(2000, 12, 31, tzinfo=ZoneInfo('UTC')), price=4)

    actual = AccountWorth.objects.have()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['have'] == 2

    assert actual[1]['year'] == 2000
    assert actual[1]['id'] == 1
    assert actual[1]['have'] == 4


# ---------------------------------------------------------------------------------------
#                                                                             SavingWorth
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

    assert SavingBalance.objects.count() == 1

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == 'Savings'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fee == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0
    assert actual.market_value == 0.5


def test_saving_worth_post_save_new():
    SavingBalanceFactory(incomes=2, fee=0)

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == 'Savings'
    assert actual.fee == 0.0
    assert actual.invested == 2.3
    assert actual.incomes == 2.0
    assert actual.market_value == 2.5

    SavingWorthFactory(price=3)

    assert SavingBalance.objects.count() == 1

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == 'Savings'
    assert actual.fee == 0.0
    assert actual.invested == 2.0
    assert actual.incomes == 2.0
    assert actual.market_value == 3.0


def test_saving_worth_have():
    SavingWorthFactory(date=dt(1970, 1, 1, tzinfo=ZoneInfo('UTC')), price=1)
    SavingWorthFactory(date=dt(1970, 12, 31, tzinfo=ZoneInfo('UTC')), price=2)
    SavingWorthFactory(date=dt(2000, 1, 1, tzinfo=ZoneInfo('UTC')), price=3)
    SavingWorthFactory(date=dt(2000, 12, 31, tzinfo=ZoneInfo('UTC')), price=4)

    actual = SavingWorth.objects.have()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['have'] == 2

    assert actual[1]['year'] == 2000
    assert actual[1]['id'] == 1
    assert actual[1]['have'] == 4


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

    assert actual[0]['title'] == 'PensionType'
    assert actual[0]['have'] == Decimal('2.15')
    assert actual[0]['latest_check'].year == 1999
    assert actual[0]['latest_check'].month == 1
    assert actual[0]['latest_check'].day == 1


def test_pension_worth_queries(pensions_worth,
                               django_assert_num_queries,):
    with django_assert_num_queries(2):
        list(PensionWorth.objects.items())


def test_pension_worth_post_save():
    PensionWorthFactory()

    assert PensionBalance.objects.count() == 1

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == 'PensionType'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fee == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0
    assert actual.market_value == 0.5


def test_pension_worth_post_save_new():
    PensionBalanceFactory()

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == 'PensionType'
    assert actual.market_value == 2.5

    PensionWorthFactory(price=3)

    assert PensionBalance.objects.count() == 1

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == 'PensionType'
    assert actual.market_value == 3.0


def test_pension_worth_have():
    PensionWorthFactory(date=dt(1970, 1, 1, tzinfo=ZoneInfo('UTC')), price=1)
    PensionWorthFactory(date=dt(1970, 12, 31, tzinfo=ZoneInfo('UTC')), price=2)
    PensionWorthFactory(date=dt(2000, 1, 1, tzinfo=ZoneInfo('UTC')), price=3)
    PensionWorthFactory(date=dt(2000, 12, 31, tzinfo=ZoneInfo('UTC')), price=4)

    actual = PensionWorth.objects.have()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['have'] == 2

    assert actual[1]['year'] == 2000
    assert actual[1]['id'] == 1
    assert actual[1]['have'] == 4
