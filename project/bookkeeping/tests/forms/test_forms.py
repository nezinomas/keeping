from datetime import datetime, timezone

import pytest
import time_machine

from ....accounts.tests.factories import AccountFactory
from ....pensions.tests.factories import PensionTypeFactory
from ...forms import AccountWorthForm, PensionWorthForm, SavingWorthForm
from ..factories import SavingTypeFactory

pytestmark = pytest.mark.django_db


WORTH_FORMS = pytest.mark.parametrize(
    "form_class, factory, field",
    [
        pytest.param(SavingWorthForm, SavingTypeFactory, "saving_type", id="saving"),
        pytest.param(AccountWorthForm, AccountFactory, "account", id="account"),
        pytest.param(
            PensionWorthForm, PensionTypeFactory, "pension_type", id="pension"
        ),
    ],
)


@WORTH_FORMS
def test_worth_form_fields(main_user, form_class, factory, field):
    form = form_class(user=main_user).as_p()

    assert '<input type="text" name="price"' in form
    assert f'<select name="{field}"' in form


def test_saving_worth_current_user_types(main_user, second_user):
    SavingTypeFactory(title="T1")
    SavingTypeFactory(title="T2", journal=second_user.journal)

    form = SavingWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@WORTH_FORMS
@time_machine.travel("1999-2-2 03:02:01")
def test_worth_form_valid_data(main_user, form_class, factory, field):
    related = factory()

    form = form_class(
        user=main_user,
        data={"date": "1999-1-2", "price": "0.01", field: related.pk},
    )
    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.serializable_value(field) == related.pk


@WORTH_FORMS
@time_machine.travel("1999-2-2 03:02:01")
def test_worth_form_price_accepts_a_decimal_comma(
    main_user, form_class, factory, field
):
    related = factory()

    form = form_class(
        user=main_user,
        data={"date": "1999-1-2", "price": "12,1", field: related.pk},
    )

    assert form.is_valid(), form.errors
    assert form.save().price == 1210


@WORTH_FORMS
@time_machine.travel("1999-2-2 03:02:01")
def test_worth_form_valid_data_reset(main_user, form_class, factory, field):
    related = factory()

    form = form_class(
        user=main_user,
        data={"date": "1999-1-2", "price": "0", field: related.pk},
    )
    assert form.is_valid()

    data = form.save()

    assert data.price == 0


@WORTH_FORMS
def test_worth_form_blank_data(main_user, form_class, factory, field):
    form = form_class(user=main_user, data={})

    assert not form.is_valid()

    assert field in form.errors


@pytest.mark.parametrize(
    "year, listed",
    [
        pytest.param(3000, False, id="closed_in_past"),
        pytest.param(1000, True, id="closed_in_future"),
        pytest.param(2000, True, id="closed_in_current_year"),
    ],
)
def test_saving_form_lists_a_type_until_its_closing_year(main_user, year, listed):
    main_user.year = year

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingWorthForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert ("S2" in str(form["saving_type"])) is listed


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


def test_account_worth_current_user_types(main_user, second_user):
    AccountFactory(title="T1")
    AccountFactory(title="T2", journal=second_user.journal)

    form = AccountWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


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


def test_pension_worth_current_user_types(main_user, second_user):
    PensionTypeFactory(title="T1")
    PensionTypeFactory(title="T2", journal=second_user.journal)

    form = PensionWorthForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form
