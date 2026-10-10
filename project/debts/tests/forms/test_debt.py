from datetime import date

import pytest
import time_machine
from django.forms.models import model_to_dict

from ....accounts.tests.factories import AccountFactory
from ....users.tests.factories import UserFactory
from ... import forms
from .. import factories

pytestmark = pytest.mark.django_db


def test_debt_init_fields(main_user):
    form = forms.DebtForm(user=main_user, debt_type="lend").as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="account"' in form
    assert '<input type="text" name="name"' in form
    assert '<input type="text" name="price"' in form
    assert '<input type="checkbox" name="closed"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form
    assert '<input type="number" name="returned"' not in form


@pytest.mark.parametrize(
    "debt_type, label",
    [
        pytest.param("lend", "Paskolos gavėjas", id="lend"),
        pytest.param("borrow", "Paskolos davėjas", id="borrow"),
    ],
)
def test_debt_name_field_label(main_user, debt_type, label):
    form = forms.DebtForm(user=main_user, debt_type=debt_type).as_p()

    assert f'<label for="id_name">{label}:</label>' in form


@time_machine.travel("1974-01-01")
def test_debt_initial_values(main_user):
    UserFactory()

    form = forms.DebtForm(user=main_user, debt_type="lend").as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_debt_current_user_accounts(main_user, second_user):
    AccountFactory(title="A1")
    AccountFactory(title="A2", journal=second_user.journal)

    form = forms.DebtForm(user=main_user, debt_type="lend").as_p()

    assert "A1" in form
    assert "A2" not in form


def test_debt_select_first_account(main_user, second_user):
    AccountFactory(title="A1", journal=second_user.journal)

    a2 = AccountFactory(title="A2")

    form = forms.DebtForm(user=main_user, debt_type="lend").as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


@pytest.mark.parametrize(
    "name", [pytest.param("AA", id="too_short"), pytest.param("A" * 101, id="too_long")]
)
def test_debt_name_length_rejected(main_user, name):
    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        data={
            "date": "1974-01-01",
            "name": name,
            "price": "1",
            "account": AccountFactory(),
        },
    )

    assert not form.is_valid()

    assert "name" in form.errors


def test_debt_valid_data(main_user):
    a = AccountFactory()

    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        data={
            "date": "1999-01-01",
            "name": "Name",
            "price": "0.01",
            "account": a.pk,
            "closed": False,
            "remark": "Rm",
        },
    )

    assert form.is_valid()

    e = form.save()

    assert e.date == date(1999, 1, 1)
    assert e.price == 1
    assert e.returned == 0
    assert e.account == a
    assert e.remark == "Rm"
    assert not e.closed


def test_debt_price_accepts_a_decimal_comma(main_user):
    a = AccountFactory()

    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        data={
            "date": "1999-01-01",
            "name": "Name",
            "price": "12,1",
            "account": a.pk,
            "closed": False,
        },
    )

    assert form.is_valid(), form.errors
    assert form.save().price == 1210


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_debt_invalid_date(year, main_user):
    a = AccountFactory()

    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        data={
            "date": f"{year}-01-01",
            "name": "Name",
            "price": "1",
            "account": a.pk,
            "closed": False,
            "remark": "Rm",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_debt_blank_data(main_user):
    form = forms.DebtForm(user=main_user, debt_type="lend", data={})

    assert not form.is_valid()

    assert len(form.errors) == 4
    assert "date" in form.errors
    assert "name" in form.errors
    assert "price" in form.errors
    assert "account" in form.errors


def test_debt_same_name_for_diff_journal(main_user, second_user):
    factories.LendFactory(
        name="XXX",
        journal=second_user.journal,
        account=AccountFactory(journal=second_user.journal, title="a2"),
    )

    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        data={
            "date": "1999-01-04",
            "name": "XXX",
            "account": AccountFactory(),
            "price": "12",
        },
    )

    assert form.is_bound
    assert form.is_valid()


def test_debt_unique_name(main_user):
    factories.LendFactory(name="XXX")
    obj = factories.LendFactory(name="YYY")
    d = model_to_dict(obj)
    d["name"] = "XXX"

    form = forms.DebtForm(user=main_user, debt_type="lend", data=d)

    assert not form.is_valid()
    assert "name" in form.errors
    assert form.errors["name"] == ["Skolintojo vardas turi būti unikalus."]


def test_debt_unique_name_unclose_with_same_name(main_user):
    factories.LendFactory(name="XXX")

    obj = factories.LendFactory(name="XXX", closed=True)
    obj.closed = False

    form = forms.DebtForm(user=main_user, debt_type="lend", data=model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert "name" in form.errors
    assert form.errors["name"] == ["Skolintojo vardas turi būti unikalus."]


def test_debt_cant_close(main_user):
    obj = factories.LendFactory(name="Xxx", closed=True)
    form = forms.DebtForm(user=main_user, debt_type="lend", data=model_to_dict(obj))

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert "closed" in form.errors
    assert form.errors["closed"] == ["Negalite uždaryti dar negražintos skolos."]


@pytest.mark.parametrize(
    "price, errors",
    [
        pytest.param("50", {}, id="equal_to_returned"),
        pytest.param("49.99", {"price": ["Mokėtina suma viršija skolą."]}, id="below"),
    ],
)
def test_debt_price_not_below_what_is_returned(main_user, price, errors):
    obj = factories.LendFactory(price=10000, returned=5000)
    data = model_to_dict(obj) | {"price": price}

    form = forms.DebtForm(user=main_user, debt_type="lend", instance=obj, data=data)

    assert form.errors == errors


def _debt_data(account, second_user):
    return {
        "journal": second_user.journal.pk,
        "date": "1999-01-01",
        "name": "Name",
        "price": "0.01",
        "account": account.pk,
        "closed": False,
        "remark": "Rm",
    }


def test_debt_create_ignores_a_posted_journal(main_user, second_user):
    a = AccountFactory(title="Mine", journal=main_user.journal)

    form = forms.DebtForm(
        user=main_user, debt_type="lend", data=_debt_data(a, second_user)
    )

    assert form.is_valid()

    assert form.save().journal == main_user.journal


def test_debt_edit_ignores_a_posted_journal(main_user, second_user):
    a = AccountFactory(title="Mine", journal=main_user.journal)
    obj = factories.LendFactory(journal=main_user.journal, account=a)

    form = forms.DebtForm(
        user=main_user,
        debt_type="lend",
        instance=obj,
        data=_debt_data(a, second_user),
    )

    assert form.is_valid()

    form.save()
    obj.refresh_from_db()

    assert obj.journal == main_user.journal
