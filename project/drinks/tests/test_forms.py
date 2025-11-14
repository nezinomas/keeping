from datetime import date

import pytest
import time_machine
from mock import patch

from ...users.factories import UserFactory
from ..factories import DrinkFactory, DrinkTargetFactory
from ..forms import DrinkCompareForm, DrinkForm, DrinkTargetForm

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                                 Drink
# -------------------------------------------------------------------------------------
def test_drink_init(main_user):
    DrinkForm(user=main_user)


def test_drink_init_fields(main_user):
    form = DrinkForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="option"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


def test_drink_help_text(main_user):
    form = DrinkForm(user=main_user).as_p()

    assert "1 Alus = 0.5L" in form
    assert "1 Vynas = 0.75L" in form
    assert "1 Degtinė = 1L" in form
    assert "Įvedus daugiau nei 20, bus manoma kad tai yra mililitrai" in form


@time_machine.travel("1974-1-1")
def test_drink_year_initial_value(main_user):
    UserFactory()

    form = DrinkForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_drink_option_initial_value(main_user):
    UserFactory()

    form = DrinkForm(user=main_user).as_p()

    assert '<option value="beer" selected>Alus</option>' in form


@patch("project.drinks.forms.App_name", "Counter Type")
def test_drink_valid_data(main_user):
    form = DrinkForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "quantity": 1.0,
            "option": "beer",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.quantity == 2.5
    assert data.user.username == "bob"
    assert data.counter_type == "Counter Type"


@patch("project.drinks.forms.App_name", "Counter Type")
@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_drink_invalid_date(main_user, year):
    form = DrinkForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "quantity": 1.0,
            "option": "beer",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_drink_blank_data(main_user):
    form = DrinkForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "date" in form.errors
    assert "quantity" in form.errors
    assert "option" in form.errors


# -------------------------------------------------------------------------------------
#                                                                          Drink Target
# -------------------------------------------------------------------------------------
def test_drink_target_init(main_user):
    DrinkTargetForm(user=main_user)


def test_drink_target_init_fields(main_user):
    form = DrinkTargetForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="drink_type"' in form
    assert '<select name="user"' not in form


@time_machine.travel("1974-1-1")
def test_drink_target_year_initial_value(main_user):
    UserFactory()

    form = DrinkTargetForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


@pytest.mark.parametrize(
    "type, qty, expect",
    [
        ("beer", 500, 2.5),
        ("wine", 750, 8),
        ("vodka", 1000, 40),
    ],
)
def test_drink_target_valid_data(main_user, type, qty, expect):
    form = DrinkTargetForm(
        user=main_user, data={"year": 1974, "quantity": qty, "drink_type": type}
    )

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == expect
    assert data.user.username == "bob"


@pytest.mark.parametrize(
    "year",
    [
        ("2000"),
        (2000),
    ],
)
def test_drink_target_valid_data_year_field(main_user, year):
    form = DrinkTargetForm(
        user=main_user, data={"year": year, "quantity": 1, "drink_type": "beer"}
    )

    assert form.is_valid()

    data = form.save()

    assert data.year == 2000


def test_drink_target_year_validation(main_user):
    DrinkTargetFactory()

    form = DrinkTargetForm(user=main_user, data={"year": 1999, "quantity": 200})

    assert not form.is_valid()

    assert "year" in form.errors


def test_drink_target_blank_data(main_user):
    form = DrinkTargetForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "year" in form.errors
    assert "quantity" in form.errors
    assert "drink_type" in form.errors


# -------------------------------------------------------------------------------------
#                                                                          Drink Filter
# -------------------------------------------------------------------------------------
def test_drink_filter_init():
    DrinkCompareForm()


def test_drink_filter_init_fields():
    form = DrinkCompareForm().as_p()

    assert '<input type="number" name="year1"' in form
    assert '<input type="number" name="year2"' in form


@time_machine.travel("1999-01-01")
def test_drink_filter_initial_values():
    form = DrinkCompareForm().as_p()

    assert '<input type="number" name="year2" value="1999"' in form


@pytest.mark.parametrize(
    "year1, year2",
    [
        (None, None),
        ("", ""),
        (None, 1111),
        ("", 1111),
        (1111, None),
        (1111, ""),
        (111, 111),
        (11111, 11111),
        ("xxx", "xxx"),
    ],
)
def test_drink_filter_form_invalid(main_user, year1, year2):
    form = DrinkCompareForm(
        user=main_user,
        data={
            "year1": year1,
            "year2": year2,
        },
    )

    assert not form.is_valid()


@pytest.mark.parametrize(
    "year1, year2, valid",
    [
        (2000, 2001, False),
        (2001, 2001, False),
        (2001, 2002, False),
        (2002, 2003, False),
        (2000, 2003, True),
    ],
)
def test_drink_filter_clean_years_fields(main_user, year1, year2, valid):
    DrinkFactory(date=date(2000, 1, 1))
    DrinkFactory(date=date(2003, 1, 1))

    form = DrinkCompareForm(
        user=main_user,
        data={
            "year1": year1,
            "year2": year2,
        },
    )

    assert form.is_valid() == valid
