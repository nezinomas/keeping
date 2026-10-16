from datetime import date

import pytest

from ...expenses.forms import ExpenseForm
from ...incomes.forms import IncomeForm
from ...savings.forms import SavingForm
from ...transactions.forms import SavingCloseForm, TransactionForm
from ..forms import AccountForm
from .factories import AccountFactory

TODAY = date(1999, 2, 2)

pytestmark = pytest.mark.django_db


def test_account_form_has_fields(main_user):
    form = AccountForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="number" name="order"' in form
    assert '<input type="text" name="closed"' in form
    assert '<select name="user"' not in form


@pytest.mark.parametrize(
    "closed",
    ["2000", 2000],
)
def test_account_valid_data(main_user, closed):
    form = AccountForm(
        data={
            "title": "Title",
            "order": "1",
            "closed": closed,
        },
        user=main_user,
        today=TODAY,
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.order == 1
    assert data.closed == 2000
    assert data.journal.users.first().username == "bob"


def test_account_blank_data(main_user):
    form = AccountForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert "title" in form.errors
    assert "order" in form.errors


def test_account_identical_title_names_the_existing_one(main_user):
    AccountFactory(title="Būstas")

    form = AccountForm(user=main_user, today=TODAY, data={"title": "Būstas"})

    assert not form.is_valid()
    assert form.errors["title"] == ["„Būstas“ jau yra."]


@pytest.mark.parametrize(
    "form_class, field",
    [
        (IncomeForm, "account"),
        (ExpenseForm, "account"),
        (TransactionForm, "from_account"),
        (SavingCloseForm, "to_account"),
        (SavingForm, "account"),
    ],
    ids=["incomes", "expenses", "transactions", "saving_close", "saving"],
)
@pytest.mark.parametrize(
    "year, closed_listed",
    [
        (3000, False),
        (1000, True),
        (2000, True),
    ],
    ids=["after_closed", "before_closed", "closed_year"],
)
def test_account_closed_in_year(main_user, form_class, field, year, closed_listed):
    main_user.year = year

    AccountFactory(title="S1")
    AccountFactory(title="S2", closed=2000)

    actual = str(form_class(user=main_user, today=TODAY, data={})[field])

    assert "S1" in actual
    assert ("S2" in actual) is closed_listed


@pytest.mark.parametrize(
    "year",
    [3000, 1000, 2000],
    ids=["after_closed", "before_closed", "closed_year"],
)
def test_transaction_to_account_lists_no_account(main_user, year):
    main_user.year = year

    AccountFactory(title="S1")
    AccountFactory(title="S2", closed=2000)

    actual = str(TransactionForm(user=main_user, today=TODAY, data={})["to_account"])

    assert "S1" not in actual
    assert "S2" not in actual


def test_account_title_empty_slug(main_user):
    form = AccountForm(user=main_user, today=TODAY, data={"title": "..."})

    assert not form.is_valid()

    assert form.errors["title"] == [
        "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."
    ]


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
def test_account_ignores_a_posted_journal(main_user, second_user, editing):
    obj = AccountFactory(title="Mine", journal=main_user.journal) if editing else None

    form = AccountForm(
        user=main_user,
        today=TODAY,
        instance=obj,
        data={
            "journal": second_user.journal.pk,
            "title": "Mine",
            "order": "1",
            "closed": "",
        },
    )

    assert form.is_valid()

    assert form.save().journal == main_user.journal
