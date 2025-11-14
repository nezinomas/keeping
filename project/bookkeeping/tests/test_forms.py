from datetime import datetime, timezone

import pytest
import pytz
import time_machine

from ...accounts.factories import AccountFactory
from ...pensions.factories import PensionTypeFactory
from ..factories import SavingTypeFactory
from ..forms import AccountWorthForm, PensionWorthForm, SavingWorthForm

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                          Saving Worth
# -------------------------------------------------------------------------------------
def test_saving_worth_init(main_user):
    SavingWorthForm(user=main_user)


def test_saving_worth_init_fields(main_user):
    form = SavingWorthForm(user=main_user).as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="saving_type"' in form


def test_saving_worth_current_user_types(main_user, second_user):
    SavingTypeFactory(title="T1")  # user bob, current user
    SavingTypeFactory(title="T2", journal=second_user.journal)  # user tom

    form = SavingWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@time_machine.travel("1999-2-2 03:02:01")
def test_saving_worth_valid_data(main_user):
    t = SavingTypeFactory()

    form = SavingWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0.01",
            "saving_type": t.pk,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.saving_type.title == t.title


@time_machine.travel("1999-2-2 03:02:01")
def test_saving_worth_valid_data_reset(main_user):
    t = SavingTypeFactory()

    form = SavingWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0",
            "saving_type": t.pk,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.price == 0


def test_saving_blank_data(main_user):
    form = SavingWorthForm(user=main_user, data={})

    assert not form.is_valid()

    assert "saving_type" in form.errors


def test_saving_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingWorthForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" not in str(form["saving_type"])


def test_saving_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingWorthForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


def test_saving_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingWorthForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


@pytest.mark.parametrize(
    "closed, date, valid",
    [
        ("1999", "2000-1-1", False),
        ("1999", "1999-12-31", True),
        ("1999", "1998-12-31", True),
    ],
)
def test_saving_worth_account_closed_date(closed, date, valid, main_user):
    a = SavingTypeFactory(closed=closed)

    form = SavingWorthForm(
        user=main_user,
        data={
            "date": date,
            "price": "1.0",
            "saving_type": a.pk,
        },
    )

    if valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert "date" in form.errors
        assert form.errors["date"][0] == "Sąskaita uždaryta 1999."


# -------------------------------------------------------------------------------------
#                                                                         Account Worth
# -------------------------------------------------------------------------------------
def test_account_worth_init(main_user):
    AccountWorthForm(user=main_user)


def test_account_worth_init_fields(main_user):
    form = AccountWorthForm(user=main_user).as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="account"' in form


def test_account_worth_current_user_types(main_user, second_user):
    AccountFactory(title="T1")  # user bob, current user
    AccountFactory(title="T2", journal=second_user.journal)  # user tom

    form = AccountWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@time_machine.travel("1999-01-02 03:02:01")
def test_account_worth_valid_data(main_user):
    a = AccountFactory()

    form = AccountWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0.01",
            "account": a.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.account.title == a.title


@time_machine.travel("1999-01-02 03:02:01")
def test_account_worth_valid_data_reset(main_user):
    a = AccountFactory()

    form = AccountWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0",
            "account": a.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.price == 0


def test_account_worth_blank_data(main_user):
    form = AccountWorthForm(user=main_user, data={})

    assert not form.is_valid()

    assert "account" in form.errors


@pytest.mark.parametrize(
    "closed, date, valid",
    [
        ("1999", "2000-1-1", False),
        ("1999", "1999-12-31", True),
        ("1999", "1998-12-31", True),
    ],
)
def test_account_worth_account_closed_date(closed, date, valid, main_user):
    a = AccountFactory(closed=closed)

    form = AccountWorthForm(
        user=main_user,
        data={
            "date": date,
            "price": "1.0",
            "account": a.pk,
        },
    )

    if valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert "date" in form.errors
        assert form.errors["date"][0] == "Sąskaita uždaryta 1999."


# -------------------------------------------------------------------------------------
#                                                                         Pension Worth
# -------------------------------------------------------------------------------------
def test_pension_worth_init(main_user):
    PensionWorthForm(user=main_user)


def test_pension_worth_init_fields(main_user):
    form = PensionWorthForm(user=main_user).as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="pension_type"' in form


def test_pension_worth_current_user_types(main_user, second_user):
    PensionTypeFactory(title="T1")  # user bob, current user
    PensionTypeFactory(title="T2", journal=second_user.journal)  # user tom

    form = PensionWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@time_machine.travel("1999-12-12 3:2:1")
def test_pension_worth_valid_data(main_user):
    p = PensionTypeFactory()

    form = PensionWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0.01",
            "pension_type": p.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.pension_type.title == p.title


@time_machine.travel("1999-12-12 3:2:1")
def test_pension_worth_valid_data_reset(main_user):
    p = PensionTypeFactory()

    form = PensionWorthForm(
        user=main_user,
        data={
            "date": "1999-1-2",
            "price": "0",
            "pension_type": p.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.price == 0


def test_pension_worth_blank_data(main_user):
    form = PensionWorthForm(user=main_user, data={})

    assert not form.is_valid()

    assert "pension_type" in form.errors
