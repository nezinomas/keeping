from datetime import date

import pytest
import time_machine

from ...accounts.tests.factories import AccountFactory
from ...savings.models import SavingType
from ...savings.tests.factories import SavingTypeFactory
from ...users.tests.factories import UserFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_init(main_user):
    TransactionForm(user=main_user)


def test_transaction_init_fields(main_user):
    form = TransactionForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="price"' in form
    assert '<select name="from_account"' in form
    assert '<select name="to_account"' in form


@time_machine.travel("1974-01-01")
def test_transaction_year_initial_value(main_user):
    UserFactory()

    form = TransactionForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_transaction_current_user_accounts(main_user, second_user):
    AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = TransactionForm(user=main_user).as_p()

    assert "A1" in form
    assert "A2" not in form


def test_transaction_current_user_accounts_selected_parent(main_user, second_user):
    a1 = AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = TransactionForm(user=main_user, data={"from_account": a1.pk}).as_p()

    assert '<option value="1" selected>A1</option>' in form
    assert '<option value="1">A1</option>' not in form


def test_transaction_valid_data(main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_transaction_invalid_date(year, main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_transaction_blank_data(main_user):
    form = TransactionForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_transaction_price_null(main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_init(main_user):
    SavingChangeForm(user=main_user)


def test_saving_change_fields(main_user):
    form = SavingChangeForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="to_account"' in form
    assert '<select name="from_account"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="number" name="fee"' in form
    assert '<input type="checkbox" name="close"' in form


@time_machine.travel("1974-01-01")
def test_saving_change_year_initial_value(main_user):
    UserFactory()

    form = SavingChangeForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_change_current_user(main_user, second_user):
    SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingChangeForm(user=main_user).as_p()

    assert "S1" in form
    assert "S2" not in form


def test_saving_change_current_user_accounts_selected_parent(main_user, second_user):
    s1 = SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingChangeForm(user=main_user, data={"from_account": s1.pk}).as_p()

    assert '<option value="1" selected>S1</option>' in form
    assert '<option value="1">S1</option>' not in form


def test_saving_change_valid_data(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_change_valid_data_with_no_fee(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_change_invalid_date(year, main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
            "fee": "0.25",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_saving_change_blank_data(main_user):
    form = SavingChangeForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_saving_change_price_null(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


def test_saving_change_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" not in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


def test_saving_change_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


def test_saving_change_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


@time_machine.travel("1999-1-1")
def test_saving_change_save_and_close_from_account(main_user):
    a_from = SavingTypeFactory(title="From")
    a_to = SavingTypeFactory(title="To")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
            "close": True,
        },
    )
    assert form.is_valid()

    form.save()

    actual = SavingType.objects.get(title=a_from.title)

    assert actual.closed == 1999


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_init(main_user):
    SavingCloseForm(user=main_user)


def test_saving_close_fields(main_user):
    form = SavingCloseForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="to_account"' in form
    assert '<select name="from_account"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="number" name="fee"' in form
    assert '<input type="checkbox" name="close"' in form


@time_machine.travel("1974-01-01")
def test_saving_close_year_initial_value(main_user):
    UserFactory()

    form = SavingCloseForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_close_current_user_saving_types(main_user, second_user):
    SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingCloseForm(user=main_user).as_p()

    assert "S1" in form
    assert "S2" not in form


def test_saving_close_current_user_accounts(main_user, second_user):
    AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = SavingCloseForm(user=main_user).as_p()

    assert "A1" in form
    assert "A2" not in form


def test_saving_close_valid_data(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_close_valid_data_no_fee(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_close_in_valid_date(year, main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
            "fee": "0.25",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_saving_close_blank_data(main_user):
    form = SavingCloseForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_saving_close_price_null(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


def test_saving_close_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" not in str(form["from_account"])


def test_saving_close_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])


def test_saving_close_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])


@time_machine.travel("1999-1-1")
def test_saving_close_save_and_close_saving_account(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
            "close": True,
        },
    )

    assert form.is_valid()

    form.save()

    actual = SavingType.objects.get(title=a_from.title)

    assert actual.closed == 1999
