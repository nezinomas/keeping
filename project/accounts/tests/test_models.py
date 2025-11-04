import pytest
from django.urls import reverse

from ...journals.factories import JournalFactory
from ..factories import AccountBalanceFactory, AccountFactory
from ..models import Account, AccountBalance

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                      Account
# ----------------------------------------------------------------------------
def test_account_model_str():
    actual = AccountFactory.build()

    assert str(actual) == "Account1"


def test_get_absolute_url():
    obj = AccountFactory()

    assert obj.get_absolute_url() == reverse("accounts:update", kwargs={"pk": obj.pk})


def test_account_items_current_journal(main_user, second_user):
    AccountFactory(title="A1")
    AccountFactory(title="A2", journal=second_user.journal)

    actual = Account.objects.items(main_user, main_user.year)

    assert len(actual) == 1
    assert str(actual[0]) == "A1"
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].journal.title == "bob Journal"


def test_account_closed_in_past(main_user):
    main_user.year = 3000

    AccountFactory(title="A1", journal=main_user.journal)
    AccountFactory(title="A2", journal=main_user.journal, closed=2000)

    actual = Account.objects.items(main_user, main_user.year)

    assert actual.count() == 1


def test_account_closed_in_future(main_user):
    main_user.year = 1000

    AccountFactory(title="A1")
    AccountFactory(title="A2", closed=2000)
    actual = Account.objects.items(main_user, main_user.year)

    assert actual.count() == 2


def test_account_closed_in_current_year(main_user):
    main_user.year = 2000

    AccountFactory(title="A1")
    AccountFactory(title="A2", closed=2000)

    actual = Account.objects.items(main_user, main_user.year)

    assert actual.count() == 2


def test_account_items_current_journal_with_year(main_user, second_user):
    AccountFactory(title="A1")
    AccountFactory(title="A2", journal=second_user.journal)

    actual = Account.objects.items(main_user, year=main_user.year)

    assert len(actual) == 1
    assert str(actual[0]) == "A1"
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].journal.title == "bob Journal"


def test_account_closed_in_past_with_year(main_user):
    AccountFactory(title="A1", journal=main_user.journal)
    AccountFactory(title="A2", journal=main_user.journal, closed=2000)

    actual = Account.objects.items(main_user, year=3000)

    assert actual.count() == 1


def test_account_closed_in_future_with_year(main_user):
    AccountFactory(title="A1")
    AccountFactory(title="A2", closed=2000)

    actual = Account.objects.items(main_user, year=1000)

    assert actual.count() == 2


def test_account_closed_in_current_year_with_year(main_user):
    main_user.year = 2000

    AccountFactory(title="A1")
    AccountFactory(title="A2", closed=2000)

    actual = Account.objects.items(main_user, year=1999)

    assert actual.count() == 2


@pytest.mark.xfail
def test_account_unique_for_journal():
    j = JournalFactory()
    Account.objects.create(title="T1", journal=j)
    Account.objects.create(title="T1", journal=j)


def test_account_unique_for_journals():
    j1 = JournalFactory(title="J1")
    j2 = JournalFactory(title="J2")

    Account.objects.create(title="T1", journal=j1)
    Account.objects.create(title="T1", journal=j2)


# ----------------------------------------------------------------------------
#                                                              Account Balance
# ----------------------------------------------------------------------------
def test_account_balance_str():
    actual = AccountBalanceFactory.build()

    assert str(actual) == "Account1"


def test_account_balance_init():
    actual = AccountBalanceFactory.build()

    assert str(actual.account) == "Account1"

    assert actual.year == 1999
    assert actual.past == 1
    assert actual.incomes == 675
    assert actual.expenses == 65
    assert actual.balance == 125
    assert actual.have == 20
    assert actual.delta == -105


def test_account_balance_items(main_user):
    AccountBalanceFactory(year=1998)
    AccountBalanceFactory(year=1999)
    AccountBalanceFactory(year=2000)

    actual = AccountBalance.objects.year(main_user, 1999)

    assert len(actual) == 1


def test_account_balance_sorting(main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    AccountBalanceFactory(year=2000, account=a2)
    AccountBalanceFactory(year=1999, account=a2)
    AccountBalanceFactory(year=2000, account=a1)
    AccountBalanceFactory(year=1999, account=a1)

    actual = AccountBalance.objects.related(main_user)

    assert actual[0].year == 1999
    assert actual[0].account == a1
    assert actual[1].year == 1999
    assert actual[1].account == a2
    assert actual[2].year == 2000
    assert actual[2].account == a1
    assert actual[3].year == 2000
    assert actual[3].account == a2
