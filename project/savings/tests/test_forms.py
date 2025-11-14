from datetime import date

import pytest
import time_machine

from ...accounts.factories import AccountFactory
from ...journals.factories import JournalFactory
from ...users.factories import UserFactory
from ..factories import SavingTypeFactory
from ..forms import SavingForm, SavingTypeForm
from ..models import SavingType

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
def test_saving_type_init(main_user):
    SavingTypeForm(user=main_user)


def test_saving_type_init_fields(main_user):
    form = SavingTypeForm(user=main_user).as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="text" name="closed"' in form
    assert '<select name="user"' not in form


@pytest.mark.parametrize(
    "closed",
    [
        ("2000"),
        (2000),
    ],
)
def test_saving_type_valid_data(main_user, closed):
    form = SavingTypeForm(
        user=main_user,
        data={
            "title": "Title",
            "closed": closed,
            "type": "funds",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.closed == 2000
    assert data.journal.title == "bob Journal"
    assert data.journal.users.first().username == "bob"


def test_saving_type_blank_data(main_user):
    form = SavingTypeForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert "title" in form.errors
    assert "type" in form.errors


def test_saving_type_title_null(main_user):
    form = SavingTypeForm(user=main_user, data={"title": None})

    assert not form.is_valid()

    assert "title" in form.errors


def test_saving_type_title_max_symbols(main_user):
    title = "a" * 50
    form = SavingTypeForm(
        user=main_user,
        data={"title": title, "journal": JournalFactory(), "type": "funds"},
    )

    assert form.is_valid()

    form.save()

    assert SavingType.objects.first().title == title


def test_saving_type_title_too_long(main_user):
    form = SavingTypeForm(user=main_user, data={"title": "a" * 255})

    assert not form.is_valid()

    assert "title" in form.errors


def test_saving_type_title_too_short(main_user):
    form = SavingTypeForm(user=main_user, data={"title": "aa"})

    assert not form.is_valid()

    assert "title" in form.errors


def test_saving_type_closed_in_past(main_user):
    main_user.year = 3000
    main_user.save()

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingForm(user=main_user, data={})

    assert "S1" in str(form["saving_type"])
    assert "S2" not in str(form["saving_type"])


def test_saving_type_closed_in_future(main_user):
    main_user.year = 1000
    main_user.save()

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingForm(user=main_user, data={})

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


def test_saving_type_closed_in_current_year(main_user):
    main_user.year = 2000
    main_user.save()

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingForm(user=main_user, data={})

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


def test_saving_type_unique_name(main_user):
    b = SavingTypeFactory(title="XXX")

    form = SavingTypeForm(
        user=main_user,
        data={
            "title": "XXX",
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                       Saving
# ----------------------------------------------------------------------------
def test_saving_init(main_user):
    SavingForm(user=main_user)


@time_machine.travel("1974-01-01")
def test_saving_year_initial_value(main_user):
    UserFactory()

    form = SavingForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_current_user_types(main_user, second_user):
    SavingTypeFactory(title="T1")  # user bob, current user
    SavingTypeFactory(title="T2", journal=second_user.journal)  # user X

    form = SavingForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


def test_saving_current_user_accounts(main_user, second_user):
    AccountFactory(title="S1")  # user bob, current user
    AccountFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingForm(user=main_user).as_p()

    assert "S1" in form
    assert "S2" not in form


def test_saving_select_first_account(main_user, second_user):
    AccountFactory(title="S1", journal=second_user.journal)
    s2 = AccountFactory(title="S2")

    form = SavingForm(user=main_user).as_p()

    expect = f'<option value="{s2.pk}" selected>{s2}</option>'
    assert expect in form


@time_machine.travel("1999-1-1")
def test_saving_valid_data(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "fee": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@pytest.mark.parametrize(
    "price",
    [
        (""),
        (None),
        (0),
    ],
)
@time_machine.travel("1999-1-1")
def test_saving_valid_data_only_fee(main_user, price):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "price": price,
            "fee": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert not data.price
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@time_machine.travel("1999-1-1")
def test_saving_valid_data_with_no_fee(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_invalid_date(main_user, year):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "price": "10",
            "fee": "2",
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_saving_blank_data(main_user):
    form = SavingForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "price" in form.errors
    assert "account" in form.errors
    assert "saving_type" in form.errors


def test_saving_price_null_and_fee_null(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": "",
            "fee": "",
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
