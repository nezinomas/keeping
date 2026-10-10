from datetime import date

import pytest
import time_machine

from ..forms import PensionForm, PensionTypeForm
from .factories import PensionTypeFactory

pytestmark = pytest.mark.django_db


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


@pytest.mark.parametrize(
    "data",
    [{}, {"title": None}, {"title": "a" * 255}, {"title": "aa"}],
    ids=["blank", "null", "too_long", "too_short"],
)
def test_pension_type_invalid_title(main_user, data):
    form = PensionTypeForm(user=main_user, data=data)

    assert not form.is_valid()

    assert list(form.errors) == ["title"]


def test_pension_type_identical_title_names_the_existing_one(main_user):
    PensionTypeFactory(title="Būstas")

    form = PensionTypeForm(user=main_user, data={"title": "Būstas"})

    assert not form.is_valid()
    assert form.errors["title"] == ["„Būstas“ jau yra."]


def test_pension_init_fields(main_user):
    form = PensionForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="pension_type"' in form
    assert '<input type="text" name="price"' in form
    assert '<input type="text" name="fee"' in form
    assert '<textarea name="remark"' in form


def test_pension_form_lists_only_current_user_types(main_user, second_user):
    PensionTypeFactory(title="T1")
    PensionTypeFactory(title="T2", journal=second_user.journal)

    form = PensionForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


def test_pension_save_stores_cents(main_user):
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
    data.refresh_from_db()

    assert data.date == date(2000, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.pension_type.title == t.title


@pytest.mark.parametrize(
    "posted, price, fee",
    [
        ({"price": 0.01}, 1, 0),
        ({"fee": 0.01}, 0, 1),
        ({"price": "0.01", "fee": ""}, 1, 0),
        ({"price": "", "fee": "0.01"}, 0, 1),
    ],
    ids=["no_fee", "no_price", "empty_fee", "empty_price"],
)
def test_pension_blank_price_or_fee_saves_zero(main_user, posted, price, fee):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "remark": "remark",
            "pension_type": t.pk,
            **posted,
        },
    )
    assert form.is_valid()

    data = form.save()
    data.refresh_from_db()

    assert data.date == date(2000, 1, 1)
    assert data.price == price
    assert data.fee == fee
    assert data.remark == "remark"
    assert data.pension_type.title == t.title


def test_pension_price_and_fee_accept_a_decimal_comma(main_user):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "price": "12,1",
            "fee": "0,55",
            "pension_type": t.pk,
        },
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.price == 1210
    assert data.fee == 55


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


@pytest.mark.parametrize(
    "posted",
    [{"price": "0", "fee": "0"}, {"price": "-10"}, {"fee": "-10"}],
    ids=["zero", "negative_price", "negative_fee"],
)
def test_pension_price_and_fee_need_a_positive_one(main_user, posted):
    t = PensionTypeFactory()

    form = PensionForm(
        user=main_user,
        data={
            "date": "2000-01-01",
            "remark": "remark",
            "pension_type": t.pk,
            **posted,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors
    assert "fee" in form.errors


def test_pension_type_title_empty_slug(main_user):
    form = PensionTypeForm(user=main_user, data={"title": "..."})

    assert not form.is_valid()

    assert form.errors["title"] == [
        "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."
    ]


def test_pension_type_create_ignores_a_posted_journal(main_user, second_user):
    form = PensionTypeForm(
        user=main_user,
        data={"journal": second_user.journal.pk, "title": "Title"},
    )

    assert form.is_valid()

    assert form.save().journal == main_user.journal


def test_pension_type_edit_ignores_a_posted_journal(main_user, second_user):
    obj = PensionTypeFactory(title="Mine", journal=main_user.journal)

    form = PensionTypeForm(
        user=main_user,
        instance=obj,
        data={"journal": second_user.journal.pk, "title": "Mine"},
    )

    assert form.is_valid()

    form.save()
    obj.refresh_from_db()

    assert obj.journal == main_user.journal


def test_pension_rejects_a_type_of_another_journal(main_user, second_user):
    form = PensionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "pension_type": PensionTypeFactory(
                title="Theirs", journal=second_user.journal
            ).pk,
        },
    )

    assert not form.is_valid()
    assert "pension_type" in form.errors
