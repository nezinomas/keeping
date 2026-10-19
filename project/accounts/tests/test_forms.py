from datetime import UTC, date, datetime

import pytest

from ...bookkeeping.tests.factories import AccountWorthFactory
from ...bookkeeping.tests.helper import quiet_build
from ...core.tests.utils import count_queries
from ...debts.tests.factories import BorrowFactory, BorrowReturnFactory
from ...expenses.forms import ExpenseForm
from ...expenses.tests.factories import ExpenseFactory
from ...incomes.forms import IncomeForm
from ...incomes.tests.factories import IncomeFactory
from ...savings.forms import SavingForm
from ...savings.tests.factories import SavingFactory
from ...transactions.forms import SavingCloseForm, TransactionForm
from ...transactions.tests.factories import SavingCloseFactory, TransactionFactory
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
    ("field", "label"),
    [
        ("title", "Sąskaitos pavadinimas"),
        ("closed", "Uždaryta"),
        ("order", "Rūšiavimas"),
    ],
)
def test_account_form_labels(main_user, field, label):
    form = AccountForm(user=main_user, today=TODAY)

    assert form[field].label == label


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


ACCOUNT_ROWS = {
    "income": lambda account, year: IncomeFactory(
        account=account, date=date(year, 6, 1)
    ),
    "expense": lambda account, year: ExpenseFactory(
        account=account, date=date(year, 6, 1)
    ),
    "buy": lambda account, year: SavingFactory(account=account, date=date(year, 6, 1)),
    "sell_into": lambda account, year: SavingCloseFactory(
        to_account=account, date=date(year, 6, 1)
    ),
    "transfer_from": lambda account, year: TransactionFactory(
        from_account=account, date=date(year, 6, 1)
    ),
    "transfer_to": lambda account, year: TransactionFactory(
        to_account=account, date=date(year, 6, 1)
    ),
    "debt": lambda account, year: BorrowFactory(account=account, date=date(year, 6, 1)),
    "debt_return": lambda account, year: BorrowReturnFactory(
        account=account, date=date(year, 6, 1)
    ),
    "worth": lambda account, year: AccountWorthFactory(
        account=account,
        date=datetime(year, 6, 1, tzinfo=UTC),
    ),
}


def _account_form(user, account, closed):
    return AccountForm(
        user=user,
        today=TODAY,
        instance=account,
        data={"title": account.title, "order": "1", "closed": closed},
    )


@pytest.mark.parametrize("row", ACCOUNT_ROWS)
@pytest.mark.parametrize(
    "closed, errors",
    [
        (
            "2000",
            {"closed": ["Negalima uždaryti anksčiau nei 2001: tais metais yra įrašų."]},
        ),
        ("2001", {}),
        ("2005", {}),
        ("", {}),
    ],
)
def test_account_close_year_not_before_its_rows(main_user, row, closed, errors):
    account = AccountFactory(title="Closing")
    ACCOUNT_ROWS[row](account, 1999)
    ACCOUNT_ROWS[row](account, 2001)

    assert _account_form(main_user, account, closed).errors == errors


def test_account_close_year_query_count(main_user):
    def queries(account, rows):
        with quiet_build(main_user):
            for year in range(1999, 1999 + rows):
                for make in ACCOUNT_ROWS.values():
                    make(account, year)
        form = _account_form(main_user, account, "2010")
        return count_queries(form.is_valid)

    assert queries(AccountFactory(title="A2"), 2) == queries(
        AccountFactory(title="A6"), 6
    )


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
