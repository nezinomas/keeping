from datetime import date

import pytest
import time_machine
from mock import patch

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from .. import factories, forms

pytestmark = pytest.mark.django_db


def test_debt_return_init():
    forms.DebtReturnForm()


def test_debt_return_init_fields():
    form = forms.DebtReturnForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="account"' in form
    assert '<select name="debt"' in form
    assert '<input type="number" name="price"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form


@patch("project.core.lib.utils.get_request_kwargs", return_value="lend")
def test_debt_name_field_label_for_lend(mck):
    form = forms.DebtReturnForm().as_p()

    assert '<label for="id_debt">Paskolos gavėjas:</label>' in form


@patch("project.core.lib.utils.get_request_kwargs", return_value="borrow")
def test_debt_name_field_label_for_borrow(mck):
    form = forms.DebtReturnForm().as_p()

    assert '<label for="id_debt">Paskolos davėjas:</label>' in form


@time_machine.travel("2-2-2")
def test_borrow_return_year_initial_value():
    UserFactory()

    form = forms.DebtReturnForm().as_p()

    assert '<input type="text" name="date" value="1999-02-02"' in form


def test_debt_return_current_user_accounts(second_user):
    AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = forms.DebtReturnForm().as_p()

    assert "A1" in form
    assert "A2" not in form


def test_debt_return_select_first_account(second_user):
    AccountFactory(title="A1", journal=second_user.journal)

    a2 = AccountFactory(title="A2")

    form = forms.DebtReturnForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


@patch("project.core.lib.utils.get_request_kwargs", return_value="lend")
def test_lend_return_valid_data(mck):
    a = AccountFactory()
    b = factories.LendFactory()

    form = forms.DebtReturnForm(
        data={
            "date": "1999-12-02",
            "debt": b.pk,
            "price": "0.01",
            "account": a.pk,
            "remark": "Rm",
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1999, 12, 2)
    assert e.account == a
    assert e.debt == b
    assert e.price == 1
    assert e.remark == "Rm"


@patch("project.core.lib.utils.get_request_kwargs", return_value="borrow")
def test_borrow_return_valid_data(mck):
    a = AccountFactory()
    b = factories.BorrowFactory()

    form = forms.DebtReturnForm(
        data={
            "date": "1999-12-02",
            "debt": b.pk,
            "price": "0.01",
            "account": a.pk,
            "remark": "Rm",
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1999, 12, 2)
    assert e.account == a
    assert e.debt == b
    assert e.price == 1
    assert e.remark == "Rm"


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_debt_return_invalid_date(year):
    a = AccountFactory()
    b = factories.LendFactory()

    form = forms.DebtReturnForm(
        data={
            "date": f"{year}-12-02",
            "debt": b.pk,
            "price": "1",
            "account": a.pk,
            "remark": "Rm",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_debt_return_blank_data():
    form = forms.DebtReturnForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 4
    assert "date" in form.errors
    assert "debt" in form.errors
    assert "account" in form.errors
    assert "price" in form.errors


@patch("project.core.lib.utils.get_request_kwargs", return_value="lend")
def test_lend_return_only_not_closed(mck):
    b1 = factories.LendFactory(closed=True)
    b2 = factories.LendFactory(closed=False)

    form = forms.DebtReturnForm().as_p()

    assert b1.name not in form
    assert b2.name in form


@patch("project.core.lib.utils.get_request_kwargs", return_value="borrow")
def test_borrow_return_only_not_closed(mck):
    b1 = factories.BorrowFactory(closed=True)
    b2 = factories.BorrowFactory(closed=False)

    form = forms.DebtReturnForm().as_p()

    assert b1.name not in form
    assert b2.name in form


def test_lend_return_price_higher(mocker):
    mocker.patch("project.core.lib.utils.get_request_kwargs", return_value="lend")

    a = AccountFactory()
    b = factories.LendFactory(price=1)

    form = forms.DebtReturnForm(
        data={
            "date": "1999-1-1",
            "debt": b.pk,
            "price": "2",
            "account": a.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert form.errors["price"] == ["Mokėtina suma viršija skolą."]


def test_borrow_return_price_higher(mocker):
    mocker.patch("project.core.lib.utils.get_request_kwargs", return_value="borrow")

    a = AccountFactory()
    b = factories.BorrowFactory(price=1)

    form = forms.DebtReturnForm(
        data={
            "date": "1999-1-1",
            "debt": b.pk,
            "price": "2",
            "account": a.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert form.errors["price"] == ["Mokėtina suma viršija skolą."]


def test_debt_return_date_earlier(mocker):
    mocker.patch("project.core.lib.utils.get_request_kwargs", return_value="lend")
    a = AccountFactory()
    b = factories.LendFactory(date=date(2001, 1, 1))

    form = forms.DebtReturnForm(
        data={
            "date": "2000-01-01",
            "debt": b.pk,
            "price": "1",
            "account": a.pk,
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert form.errors["date"] == ["Data yra ankstesnė nei skolos data."]
