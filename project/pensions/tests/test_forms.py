from datetime import date

import pytest
import time_machine

from ..forms import PensionForm, PensionTypeForm
from .factories import PensionTypeFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  PensionType
# ----------------------------------------------------------------------------
def test_pension_type_init(main_user):
    PensionTypeForm(user=main_user)


def test_pension_type_init_fields(main_user):
    form = PensionTypeForm(user=main_user).as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="user"' not in form


def test_pension_type_valid_data(main_user):
    form = PensionTypeForm(
        user=main_user,
        data={
            "title": "Title",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.journal.title == "bob Journal"
    assert data.journal.users.first().username == "bob"


def test_pension_type_blank_data(main_user):
    form = PensionTypeForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert "title" in form.errors


def test_pension_type_title_null(main_user):
    form = PensionTypeForm(user=main_user, data={"title": None})

    assert not form.is_valid()

    assert "title" in form.errors


def test_pension_type_title_too_long(main_user):
    form = PensionTypeForm(user=main_user, data={"title": "a" * 255})

    assert not form.is_valid()

    assert "title" in form.errors


def test_pension_type_title_too_short(main_user):
    form = PensionTypeForm(user=main_user, data={"title": "aa"})

    assert not form.is_valid()

    assert "title" in form.errors


def test_pensiong_type_unique_name(main_user):
    PensionTypeFactory(title="XXX")

    form = PensionTypeForm(
        user=main_user,
        data={
            "title": "XXX",
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_init(main_user):
    PensionForm(user=main_user)


def test_pension_init_fields(main_user):
    form = PensionForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="pension_type"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="number" name="fee"' in form
    assert '<textarea name="remark"' in form


def test_saving_current_user_types(main_user, second_user):
    PensionTypeFactory(title="T1")  # user bob, current user
    PensionTypeFactory(title="T2", journal=second_user.journal)  # user X

    form = PensionForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


def test_pension_valid_data(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": 0.01,
            "fee": 0.01,
            "remark": "remark",
            "pension_type": t.pk,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.pension_type.title == t.title


def test_pension_valid_data_no_price(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "fee": 0.01,
            "remark": "remark",
            "pension_type": t.pk,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert not data.price
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.pension_type.title == t.title


def test_pension_valid_data_no_fee(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": 0.01,
            "remark": "remark",
            "pension_type": t.pk,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.remark == "remark"
    assert data.pension_type.title == t.title


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_pension_invalid_date(main_user, year):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "price": "1.0",
            "fee": "0.0",
            "remark": "remark",
            "pension_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_pension_blank_data(main_user):
    form = PensionForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "price" in form.errors
    assert "fee" in form.errors
    assert "pension_type" in form.errors


def test_pension_price_and_fee_null(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": "0",
            "fee": "0",
            "remark": "remark",
            "pension_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert "fee" in form.errors


def test_pension_price_negative(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": "-10",
            "remark": "remark",
            "pension_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert "fee" in form.errors


def test_pension_fee_negative(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "fee": "-10",
            "remark": "remark",
            "pension_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert "fee" in form.errors
