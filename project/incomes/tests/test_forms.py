from datetime import date

import pytest
import time_machine

from ...accounts.tests.factories import AccountFactory
from ..forms import IncomeForm, IncomeTypeForm
from .factories import IncomeTypeFactory

pytestmark = pytest.mark.django_db


def test_income_type_init_fields(main_user):
    form = IncomeTypeForm(user=main_user).as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="type"' in form
    assert '<select name="user"' not in form


def test_income_type_valid_data(main_user):
    form = IncomeTypeForm(
        user=main_user,
        data={
            "title": "Title",
            "type": "salary",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.type == "salary"
    assert data.journal == main_user.journal


def test_income_type_blank_data(main_user):
    form = IncomeTypeForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert "title" in form.errors
    assert "type" in form.errors


@pytest.mark.parametrize(
    "title",
    [None, "a" * 255, "aa"],
    ids=["null", "too_long", "too_short"],
)
def test_income_type_title_rejected(main_user, title):
    form = IncomeTypeForm(user=main_user, data={"title": title})

    assert not form.is_valid()

    assert "title" in form.errors


@pytest.mark.parametrize(
    ("title", "existing", "message"),
    [
        ("Būstas", ["Būstas"], "„Būstas“ jau yra."),
        (
            "...",
            [],
            "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo.",
        ),
    ],
    ids=["identical_title", "empty_slug"],
)
def test_income_type_title_error(main_user, title, existing, message):
    for existing_title in existing:
        IncomeTypeFactory(title=existing_title)

    form = IncomeTypeForm(user=main_user, data={"title": title, "type": "salary"})

    assert not form.is_valid()
    assert form.errors["title"] == [message]


@time_machine.travel("1974-01-01")
def test_income_year_initial_value(main_user):
    form = IncomeForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_income_select_first_account(main_user, second_user):
    a2 = AccountFactory(title="A2")
    AccountFactory(title="A1", journal=second_user.journal)

    form = IncomeForm(user=main_user).as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


@pytest.mark.parametrize(
    ("posted", "cents"), [(0.01, 1), ("12,1", 1210)], ids=["dot", "decimal_comma"]
)
def test_income_valid_data(main_user, posted, cents):
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": posted,
            "remark": "remark",
            "account": a.pk,
            "income_type": t.pk,
        },
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == cents
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.income_type.title == t.title


def test_income_blank_data(main_user):
    form = IncomeForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "price" in form.errors
    assert "account" in form.errors
    assert "income_type" in form.errors


def test_income_price_null(main_user):
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": "0",
            "remark": "remark",
            "account": a.pk,
            "income_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
def test_income_type_ignores_a_posted_journal(main_user, second_user, editing):
    obj = (
        IncomeTypeFactory(title="Mine", journal=main_user.journal) if editing else None
    )

    form = IncomeTypeForm(
        user=main_user,
        instance=obj,
        data={"journal": second_user.journal.pk, "title": "Mine", "type": "salary"},
    )

    assert form.is_valid()

    assert form.save().journal == main_user.journal


@pytest.mark.parametrize("field", ["account", "income_type"])
def test_income_rejects_an_account_or_type_of_another_journal(
    main_user, second_user, field
):
    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "account": AccountFactory(title="Mine", journal=main_user.journal).pk,
        "income_type": IncomeTypeFactory(title="Mine", journal=main_user.journal).pk,
    }
    foreign = {
        "account": AccountFactory(title="Theirs", journal=second_user.journal),
        "income_type": IncomeTypeFactory(title="Theirs", journal=second_user.journal),
    }
    data[field] = foreign[field].pk

    form = IncomeForm(user=main_user, data=data)

    assert not form.is_valid()
    assert field in form.errors
