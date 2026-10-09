from datetime import date

import pytest
import time_machine

from ..forms import CountForm, CountTypeForm
from .factories import CountTypeFactory

pytestmark = pytest.mark.django_db


def test_form_init_fields(main_user):
    form = CountForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form
    assert '<select name="count_type"' in form


@time_machine.travel("1974-01-01")
def test_form_year_initial_value(main_user):
    form = CountForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert '<input type="number" name="quantity" value="1"' in form


def test_form_valid_data(main_user):
    obj = CountTypeFactory(title="Xxx")

    form = CountForm(
        user=main_user, data={"date": "1999-01-01", "count_type": obj, "quantity": 1.0}
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == "bob"
    assert data.count_type.title == "Xxx"
    assert data.count_type.slug == "xxx"


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_form_invalid_date(year, main_user):
    obj = CountTypeFactory(title="xxx")

    form = CountForm(
        user=main_user,
        data={"date": f"{year}-01-01", "count_type": obj, "quantity": 1.0},
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_form_blank_data(main_user):
    form = CountForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "date" in form.errors
    assert "quantity" in form.errors
    assert "count_type" in form.errors


def test_form_no_count_type(main_user):
    form = CountForm(user=main_user, data={"date": "1999-01-01", "quantity": 1.0})

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert "count_type" in form.errors
    assert "Šis laukas yra privalomas." in form.errors["count_type"]


def test_count_type_init_fields():
    form = CountTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="user"' not in form


def test_count_type_valid_data(main_user):
    form = CountTypeForm(user=main_user, data={"title": "XXXXX"})

    assert form.is_valid()

    data = form.save()

    assert data.user.username == "bob"
    assert data.title == "XXXXX"


def test_count_type_blank_data(main_user):
    form = CountTypeForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert "title" in form.errors


@pytest.mark.parametrize(
    "existing, title, errors",
    [
        pytest.param(
            [],
            "---",
            ["Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."],
            id="empty_slug",
        ),
        pytest.param(
            [],
            "Pienas ½ l",
            ["Pavadinime negali būti „½“."],
            id="expanding_character",
        ),
        pytest.param(
            ["Būstas"],
            "Būstas",
            ["„Būstas“ jau yra."],
            id="identical_title_names_the_existing_one",
        ),
        pytest.param(
            ["Būstas"],
            "Bustas",
            ["Pavadinimas per daug panašus į jau esantį „Būstas“."],
            id="slug_taken",
        ),
    ],
)
def test_count_type_title_rejected(existing, title, errors, main_user):
    for existing_title in existing:
        CountTypeFactory(title=existing_title, user=main_user)

    form = CountTypeForm(user=main_user, data={"title": title})

    assert not form.is_valid()
    assert form.errors["title"] == errors


@pytest.mark.parametrize(
    "title",
    [
        "none",
        "None",
        "type",
        "Type",
        "update",
        "Update",
        "delete",
        "Delete",
        "index",
        "Index",
        "data",
        "Data",
        "history",
        "History",
        "empty",
        "Empty",
    ],
)
def test_count_type_title_no_longer_collides_with_a_route(title, main_user):
    form = CountTypeForm(user=main_user, data={"title": title})

    assert form.is_valid()


def test_form_count_type_and_second_user(main_user, second_user):
    own = CountTypeFactory(title="T1")
    other = CountTypeFactory(title="T2", user=second_user)

    form = CountForm(user=main_user, data={}).as_p()

    assert f'<option value="{own.pk}">T1</option>' in form
    assert f'<option value="{other.pk}">T2</option>' not in form


def test_form_load_select_count_type(main_user):
    selected = CountTypeFactory(title="T1")
    CountTypeFactory(title="T2")

    form = CountForm(user=main_user, counter_type="t1").as_p()

    assert f'<option value="{selected.pk}" selected>T1</option>' in form


def test_count_type_same_slug_for_second_user_is_valid(main_user, second_user):
    CountTypeFactory(title="Būstas", user=second_user)

    form = CountTypeForm(user=main_user, data={"title": "Bustas"})

    assert form.is_valid()


@pytest.mark.parametrize("title", ["Būstas", "BŪSTAS"])
def test_count_type_edit_keeping_its_slug_is_valid(title, main_user):
    count_type = CountTypeFactory(title="Būstas", user=main_user)

    form = CountTypeForm(user=main_user, instance=count_type, data={"title": title})

    assert form.is_valid()
