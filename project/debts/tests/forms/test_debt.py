from datetime import date

import pytest
from django.forms.models import model_to_dict

from ....accounts.tests.factories import AccountFactory
from ....users.tests.factories import UserFactory
from ... import forms
from .. import factories

TODAY = date(2000, 2, 2)

pytestmark = pytest.mark.django_db


def test_debt_init_fields(main_user):
    form = forms.DebtForm(user=main_user, today=TODAY, debt_type="lend").as_p()

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
    form = forms.DebtForm(user=main_user, today=TODAY, debt_type=debt_type).as_p()

    assert f'<label for="id_name">{label}:</label>' in form


def test_debt_initial_values(main_user):
    UserFactory()

    form = forms.DebtForm(
        user=main_user, today=date(1974, 1, 1), debt_type="lend"
    ).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_debt_select_first_account(main_user, second_user):
    AccountFactory(title="A1", journal=second_user.journal)

    a2 = AccountFactory(title="A2")

    form = forms.DebtForm(user=main_user, today=TODAY, debt_type="lend").as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form
    assert "A1" not in form


@pytest.mark.parametrize(
    "name, error",
    [
        pytest.param(
            "AA",
            "Įsitikinkite, kad reikšmė sudaryta iš nemažiau kaip 3 ženklų "
            "(dabartinis ilgis 2).",
            id="too_short",
        ),
        pytest.param(
            "A" * 101,
            "Įsitikinkite, kad reikšmė sudaryta iš nedaugiau kaip 100 ženklų "
            "(dabartinis ilgis 101).",
            id="too_long",
        ),
    ],
)
def test_debt_name_length_rejected(main_user, name, error):
    form = forms.DebtForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        data={
            "date": "1999-01-01",
            "name": name,
            "price": "1",
            "account": AccountFactory(),
        },
    )

    assert form.errors == {"name": [error]}


@pytest.mark.parametrize(
    "price, cents",
    [
        pytest.param("0.01", 1, id="point"),
        pytest.param("12,1", 1210, id="decimal_comma"),
    ],
)
def test_debt_valid_data(main_user, price, cents):
    a = AccountFactory()

    form = forms.DebtForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        data={
            "date": "1999-01-01",
            "name": "Name",
            "price": price,
            "account": a.pk,
            "closed": False,
            "remark": "Rm",
        },
    )

    assert form.is_valid(), form.errors

    e = form.save()

    assert e.date == date(1999, 1, 1)
    assert e.price == cents
    assert e.returned == 0
    assert e.account == a
    assert e.remark == "Rm"
    assert not e.closed


@pytest.mark.parametrize(
    "posted, errors",
    [
        pytest.param(
            "2000-03-01",
            {
                "date": [
                    "Data negali būti vėlesnė nei sąskaitos uždarymo data. "
                    "Sąskaita buvo uždaryta 1999."
                ]
            },
            id="after_closed",
        ),
        pytest.param("1999-12-31", {}, id="closed_year"),
    ],
)
def test_debt_date_after_the_account_closed(main_user, posted, errors):
    a = AccountFactory(closed=1999)

    form = forms.DebtForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        data={"date": posted, "name": "Name", "price": "1", "account": a.pk},
    )

    assert form.errors == errors


@pytest.mark.parametrize("year", [1998, 2001])
def test_debt_invalid_date(year, main_user):
    a = AccountFactory()

    form = forms.DebtForm(
        user=main_user,
        today=date(1999, 2, 2),
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
    form = forms.DebtForm(user=main_user, today=TODAY, debt_type="lend", data={})

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
        today=TODAY,
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

    form = forms.DebtForm(user=main_user, today=TODAY, debt_type="lend", data=d)

    assert not form.is_valid()
    assert "name" in form.errors
    assert form.errors["name"] == ["Vardas turi būti unikalus."]


def test_debt_unique_name_unclose_with_same_name(main_user):
    factories.LendFactory(name="XXX")

    obj = factories.LendFactory(name="XXX", closed=True)
    obj.closed = False

    form = forms.DebtForm(
        user=main_user, today=TODAY, debt_type="lend", data=model_to_dict(obj)
    )

    assert form.is_bound
    assert not form.is_valid()
    assert "name" in form.errors
    assert form.errors["name"] == ["Vardas turi būti unikalus."]


def test_debt_cant_close(main_user):
    obj = factories.LendFactory(name="Xxx", closed=True)
    form = forms.DebtForm(
        user=main_user, today=TODAY, debt_type="lend", data=model_to_dict(obj)
    )

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert "closed" in form.errors
    assert form.errors["closed"] == ["Negalite uždaryti dar negražintos skolos."]


@pytest.mark.parametrize("price", ["abc", "0"])
def test_debt_edit_with_an_invalid_price_is_a_field_error(main_user, price):
    obj = factories.LendFactory(price=10000, returned=5000)
    data = model_to_dict(obj) | {"price": price}

    form = forms.DebtForm(
        user=main_user, today=TODAY, debt_type="lend", instance=obj, data=data
    )

    assert list(form.errors) == ["price"]


@pytest.mark.parametrize(
    "price, errors",
    [
        pytest.param("50", {}, id="equal_to_returned"),
        pytest.param(
            "49.99",
            {"price": ["Skola negali būti mažesnė nei grąžinta suma."]},
            id="below",
        ),
    ],
)
def test_debt_price_not_below_what_is_returned(main_user, price, errors):
    obj = factories.LendFactory(price=10000, returned=5000)
    data = model_to_dict(obj) | {"price": price}

    form = forms.DebtForm(
        user=main_user, today=TODAY, debt_type="lend", instance=obj, data=data
    )

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


@pytest.mark.parametrize(
    "instance_of",
    [
        pytest.param(lambda user, account: None, id="create"),
        pytest.param(
            lambda user, account: factories.LendFactory(
                journal=user.journal, account=account
            ),
            id="edit",
        ),
    ],
)
def test_debt_ignores_a_posted_journal(main_user, second_user, instance_of):
    a = AccountFactory(title="Mine", journal=main_user.journal)

    form = forms.DebtForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        instance=instance_of(main_user, a),
        data=_debt_data(a, second_user),
    )

    assert form.is_valid()

    saved = form.save()
    saved.refresh_from_db()

    assert saved.journal == main_user.journal
