import pytest
from django.db import IntegrityError
from django.urls import reverse

from ...journals.tests.factories import JournalFactory
from ...users.tests.factories import UserFactory
from ..models import Account
from ..services.model_services import AccountBalanceModelService, AccountModelService
from .factories import AccountBalanceFactory, AccountFactory

pytestmark = pytest.mark.django_db


def test_account_model_str():
    actual = AccountFactory.build()

    assert str(actual) == "Account1"


def test_get_absolute_url():
    obj = AccountFactory()

    assert obj.get_absolute_url() == reverse("accounts:update", kwargs={"pk": obj.pk})


def test_account_items_current_journal(main_user, second_user):
    AccountFactory(title="A1")
    AccountFactory(title="A2", journal=second_user.journal)

    actual = AccountModelService(main_user).items()

    assert len(actual) == 1
    assert str(actual[0]) == "A1"
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].journal.title == "bob Journal"


@pytest.mark.parametrize(
    "year, expected",
    [
        (3000, 1),
        (1000, 2),
        (2000, 2),
        (1999, 2),
    ],
    ids=["after_closed", "before_closed", "closed_year", "just_before_closed"],
)
def test_account_closed_in_year(main_user, year, expected):
    AccountFactory(title="A1", journal=main_user.journal)
    AccountFactory(title="A2", journal=main_user.journal, closed=2000)

    actual = AccountModelService(main_user).items_in(year)

    assert actual.count() == expected


def test_account_items_keep_the_accounts_open_in_the_users_year(main_user):
    AccountFactory(title="Open", journal=main_user.journal)
    AccountFactory(title="Closed this year", journal=main_user.journal, closed=1999)
    AccountFactory(title="Closed last year", journal=main_user.journal, closed=1998)

    actual = AccountModelService(main_user).items()

    assert {x.title for x in actual} == {"Open", "Closed this year"}


def test_account_unique_for_journals():
    # an account's save syncs its balances for the journal's user
    for title in ("J1", "J2"):
        journal = JournalFactory(title=title)
        UserFactory(username=title, email=f"{title}@u.u", journal=journal)
        Account.objects.create(title="T1", journal=journal)

    assert Account.objects.filter(title="T1").count() == 2


@pytest.mark.parametrize(
    "first, second",
    [
        ("T1", "T1"),
        ("Būstas", "Bustas"),
    ],
    ids=["same_title", "same_slug"],
)
def test_account_unique_per_journal(first, second):
    j = JournalFactory()
    Account.objects.create(title=first, journal=j)

    with pytest.raises(IntegrityError):
        Account.objects.create(title=second, journal=j)


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

    actual = AccountBalanceModelService(main_user).year(1999)

    assert len(actual) == 1


def test_account_balance_sorting(main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    AccountBalanceFactory(year=2000, account=a2)
    AccountBalanceFactory(year=1999, account=a2)
    AccountBalanceFactory(year=2000, account=a1)
    AccountBalanceFactory(year=1999, account=a1)

    actual = AccountBalanceModelService(main_user).objects

    assert actual[0].year == 1999
    assert actual[0].account == a1
    assert actual[1].year == 1999
    assert actual[1].account == a2
    assert actual[2].year == 2000
    assert actual[2].account == a1
    assert actual[3].year == 2000
    assert actual[3].account == a2
