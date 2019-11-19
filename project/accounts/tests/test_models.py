import pytest

from ...users.factories import UserFactory
from ..factories import AccountBalanceFactory, AccountFactory
from ..models import Account, AccountBalance


# ----------------------------------------------------------------------------
#                                                                      Account
# ----------------------------------------------------------------------------
def test_account_model_str():
    actual = AccountFactory.build()

    assert str(actual) == 'Account1'


@pytest.mark.django_db
def test_account_items_current_user(get_user):
    u = UserFactory(username='XXX')

    AccountFactory(title='A1')
    AccountFactory(title='A2', user=u)

    actual = Account.objects.items()

    assert len(actual) == 1
    assert str(actual[0]) == 'A1'
    assert actual[0].user.username == 'bob'


# ----------------------------------------------------------------------------
#                                                              Account Balance
# ----------------------------------------------------------------------------
def test_account_balance_str():
    actual = AccountBalanceFactory.build()

    assert str(actual) == 'Account1'


def test_account_balance_init():
    actual = AccountBalanceFactory.build()

    assert str(actual.account) == 'Account1'

    assert actual.year == 1999
    assert actual.past == 1.0
    assert actual.incomes == 6.75
    assert actual.expenses == 6.5
    assert actual.balance == 1.25
    assert actual.have == 0.20
    assert actual.delta == -1.05


@pytest.mark.django_db
def test_account_balance_items(get_user):
    AccountBalanceFactory(year=1998)
    AccountBalanceFactory(year=1999)
    AccountBalanceFactory(year=2000)

    actual = AccountBalance.objects.year(1999)

    assert len(actual) == 1


@pytest.mark.django_db
def test_account_balance_queries(get_user, django_assert_num_queries):
    a1 = AccountFactory(title='a1')
    a2 = AccountFactory(title='a2')

    AccountBalanceFactory(account=a1)
    AccountBalanceFactory(account=a2)

    with django_assert_num_queries(1):
        list(AccountBalance.objects.items().values())


@pytest.mark.django_db
def test_account_balance_related_for_user(get_user):
    u = UserFactory(username='XXX')

    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2', user=u)

    AccountBalanceFactory(account=a1)
    AccountBalanceFactory(account=a2)

    actual = AccountBalance.objects.related()

    assert len(actual) == 1
    assert str(actual[0].account) == 'A1'
    assert actual[0].account.user.username == 'bob'
