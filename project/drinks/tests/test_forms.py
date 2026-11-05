from datetime import date

import pytest
from django.utils.translation import gettext as _

from ...users.tests.factories import UserFactory
from ..forms import (
    DrinkCompareForm,
    DrinkForm,
    DrinkTargetForm,
    QuickAddForm,
    TypicalYearForm,
)
from ..models import Drink
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db

TODAY = date(1999, 1, 1)


def test_drink_init_fields(main_user):
    form = DrinkForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="text" name="stdav"' in form
    assert '<select name="option"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


@pytest.mark.parametrize("form_class", [DrinkForm, DrinkTargetForm])
def test_quantity_rewrites_a_decimal_comma(main_user, form_class):
    form = form_class(user=main_user, today=TODAY).as_p()

    assert 'inputmode="decimal"' in form
    assert "@keyup=" in form
    assert "$el.value.replace(" in form
    assert "[^0-9.]" in form
    assert r"^(\d*\.?\d*).*" in form


@pytest.mark.parametrize("typed", ["1", "1.5", "0.75", "500", "1.", ".5"])
def test_drink_quantity_accepts_every_shape_the_widget_allows(main_user, typed):
    # the keyup filter leaves digits and one dot, so a trailing or leading dot
    # is reachable and has to parse
    form = DrinkForm(
        user=main_user,
        today=TODAY,
        data={"date": "1999-01-01", "option": "beer", "stdav": typed},
    )

    assert form.is_valid(), form.errors


def test_drink_help_text(main_user):
    form = DrinkForm(user=main_user, today=TODAY).as_p()

    assert "1 Alus = 0.5L" in form
    assert "1 Vynas = 0.75L" in form
    assert "1 Degtinė = 1L" in form
    assert "Įvedus daugiau nei 20, bus manoma kad tai yra mililitrai" in form


def test_drink_year_initial_value(main_user):
    UserFactory()

    form = DrinkForm(user=main_user, today=date(1974, 1, 1)).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_drink_date_widget(main_user):
    form = DrinkForm(user=main_user, today=TODAY)

    assert form["date"].widget_type == "datepicker"


def test_drink_option_initial_value(main_user):
    UserFactory()

    form = DrinkForm(user=main_user, today=TODAY).as_p()

    assert '<option value="beer" selected>Alus</option>' in form


def test_drink_valid_data(mocker, main_user):
    mocker.patch("project.drinks.forms.App_name", "Counter Type")

    form = DrinkForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "stdav": 1.0,
            "option": "beer",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.stdav == 2.5
    assert data.user.username == "bob"
    assert data.counter_type == "Counter Type"


@pytest.mark.parametrize(
    "ml, drink_type, expect_stdav, expect_converted_from_ml",
    [
        (1, "beer", 2.5, False),
        (21, "beer", 0.1, True),
        (500, "beer", 2.5, True),
        (1, "wine", 8, False),
        (20, "wine", 160, False),
        (21, "wine", 0.22, True),
        (750, "wine", 8, True),
        (1, "vodka", 40, False),
        (20, "vodka", 800, False),
        (21, "vodka", 0.84, True),
        (1000, "vodka", 40, True),
        (1, "stdav", 1, False),
        (20, "stdav", 20, False),
        (21, "stdav", 21, False),
    ],
)
def test_drink_recalculate_ml_on_save(
    mocker, main_user, ml, drink_type, expect_stdav, expect_converted_from_ml
):
    mocker.patch("project.drinks.forms.App_name", "Counter Type")

    form = DrinkForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "stdav": ml,
            "option": drink_type,
        },
    )

    form.save()

    actual = Drink.objects.last()

    assert actual.option == drink_type
    assert round(actual.stdav, 2) == expect_stdav
    assert actual.converted_from_ml == expect_converted_from_ml


@pytest.mark.parametrize("year", [1998, 2001])
def test_drink_invalid_date(mocker, main_user, year):
    mocker.patch("project.drinks.forms.App_name", "Counter Type")

    form = DrinkForm(
        user=main_user,
        today=date(1999, 2, 2),
        data={
            "date": f"{year}-01-01",
            "stdav": 1.0,
            "option": "beer",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_drink_blank_data(main_user):
    form = DrinkForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "date" in form.errors
    assert "stdav" in form.errors
    assert "option" in form.errors


def test_quick_add_reads_the_quantity_the_bar_posts(main_user):
    form = QuickAddForm.from_post(
        {"quantity": "2.5", "option": "beer", "date": "1999-01-01"}, main_user, TODAY
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["stdav"] == pytest.approx(6.25, rel=0.01)


def test_quick_add_without_an_option_falls_back_to_the_users_drink_type(main_user):
    main_user.drink_type = "wine"

    form = QuickAddForm.from_post(
        {"quantity": "1", "date": "1999-01-01"}, main_user, TODAY
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["option"] == "wine"


def test_quick_add_without_a_date_falls_back_to_the_header_year(main_user):
    main_user.year = 1999

    form = QuickAddForm.from_post({"quantity": "1", "option": "beer"}, main_user, TODAY)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["date"] == date(1999, 1, 1)


def test_quick_add_without_a_quantity_is_invalid(main_user):
    form = QuickAddForm.from_post(
        {"option": "beer", "date": "1999-01-01"}, main_user, TODAY
    )

    assert not form.is_valid()
    assert "stdav" in form.errors


def test_quick_add_saves_a_drink(main_user):
    form = QuickAddForm.from_post(
        {"quantity": "1", "option": "beer", "date": "1999-01-01"}, main_user, TODAY
    )
    form.save()

    assert Drink.objects.count() == 1


def test_drink_target_init_fields(main_user):
    form = DrinkTargetForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="year"' in form
    assert '<input type="text" name="quantity"' in form
    assert '<select name="drink_type"' in form
    assert '<select name="user"' not in form


def test_drink_target_year_initial_value(main_user):
    UserFactory()

    form = DrinkTargetForm(user=main_user, today=date(1974, 1, 1)).as_p()

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
        user=main_user,
        today=TODAY,
        data={"year": 1974, "quantity": qty, "drink_type": type},
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
        user=main_user,
        today=TODAY,
        data={"year": year, "quantity": 1, "drink_type": "beer"},
    )

    assert form.is_valid()

    data = form.save()

    assert data.year == 2000


def test_drink_target_year_validation(main_user):
    DrinkTargetFactory()

    form = DrinkTargetForm(
        user=main_user, today=TODAY, data={"year": 1999, "quantity": 200}
    )

    assert not form.is_valid()

    assert "year" in form.errors


def test_drink_target_blank_data(main_user):
    form = DrinkTargetForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "year" in form.errors
    assert "quantity" in form.errors
    assert "drink_type" in form.errors


@pytest.mark.parametrize(
    ("form_class", "data"),
    [
        (DrinkForm, {"date": "1999-01-01", "stdav": 1.0, "option": "beer"}),
        (DrinkTargetForm, {"year": 2000, "quantity": 1, "drink_type": "beer"}),
    ],
    ids=["drink", "drink_target"],
)
def test_a_posted_user_is_ignored(main_user, second_user, form_class, data):
    form = form_class(
        user=main_user, today=TODAY, data={**data, "user": second_user.pk}
    )

    assert form.is_valid()

    assert form.save().user == main_user


@pytest.mark.parametrize("form_class", [DrinkCompareForm, TypicalYearForm])
def test_year_forms_init_fields(main_user, form_class):
    form = form_class(user=main_user, today=TODAY).as_p()

    for field in form_class.field_order:
        assert f'<input type="number" name="{field}"' in form


@pytest.mark.parametrize(
    "form_class, first, second",
    [
        pytest.param(DrinkCompareForm, None, None, id="compare-none"),
        pytest.param(DrinkCompareForm, "", "", id="compare-blank"),
        pytest.param(DrinkCompareForm, None, 1111, id="compare-first_none"),
        pytest.param(DrinkCompareForm, "", 1111, id="compare-first_blank"),
        pytest.param(DrinkCompareForm, 1111, None, id="compare-second_none"),
        pytest.param(DrinkCompareForm, 1111, "", id="compare-second_blank"),
        pytest.param(DrinkCompareForm, 111, 111, id="compare-too_small"),
        pytest.param(DrinkCompareForm, 11111, 11111, id="compare-too_big"),
        pytest.param(DrinkCompareForm, "xxx", "xxx", id="compare-text"),
        pytest.param(TypicalYearForm, None, None, id="typical_year-none"),
        pytest.param(TypicalYearForm, "", "", id="typical_year-blank"),
        pytest.param(TypicalYearForm, None, 2000, id="typical_year-first_none"),
        pytest.param(TypicalYearForm, 2000, "", id="typical_year-second_blank"),
        pytest.param(TypicalYearForm, 111, 111, id="typical_year-too_small"),
        pytest.param(TypicalYearForm, 11111, 11111, id="typical_year-too_big"),
        pytest.param(TypicalYearForm, "xxx", "xxx", id="typical_year-text"),
    ],
)
def test_year_forms_invalid(main_user, form_class, first, second):
    data = dict(zip(form_class.field_order, (first, second), strict=True))
    form = form_class(user=main_user, today=TODAY, data=data)

    assert not form.is_valid()


def test_typical_year_boxes_open_on_the_users_full_span(main_user):
    # nothing is pooled until this form is submitted, so the boxes propose the
    # widest range there is rather than leaving the user to type one
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(2005, 1, 1))

    form = TypicalYearForm(user=main_user, today=TODAY).as_p()

    assert 'name="year_from" value="1999"' in form
    assert 'name="year_to" value="2005"' in form


@pytest.mark.parametrize(
    "form_class, first, second, valid",
    [
        pytest.param(DrinkCompareForm, 2000, 2001, False, id="compare-second_empty"),
        pytest.param(DrinkCompareForm, 2001, 2001, False, id="compare-same_year"),
        pytest.param(DrinkCompareForm, 2001, 2002, False, id="compare-both_empty"),
        pytest.param(DrinkCompareForm, 2002, 2003, False, id="compare-first_empty"),
        pytest.param(DrinkCompareForm, 2000, 2003, True, id="compare-valid"),
        pytest.param(TypicalYearForm, 2000, 2003, True, id="typical_year-valid"),
        # pooling one year is a reading, not a mistake
        pytest.param(TypicalYearForm, 2000, 2000, True, id="typical_year-one_year"),
        pytest.param(TypicalYearForm, 2003, 2003, True, id="typical_year-last_year"),
        # reversed, and never silently swapped
        pytest.param(TypicalYearForm, 2003, 2000, False, id="typical_year-reversed"),
        pytest.param(TypicalYearForm, 2001, 2003, False, id="typical_year-from_empty"),
        pytest.param(TypicalYearForm, 2000, 2002, False, id="typical_year-to_empty"),
        pytest.param(TypicalYearForm, 1999, 2003, False, id="typical_year-outside"),
    ],
)
def test_year_forms_clean_years_fields(main_user, form_class, first, second, valid):
    DrinkFactory(date=date(2000, 1, 1))
    DrinkFactory(date=date(2003, 1, 1))

    data = dict(zip(form_class.field_order, (first, second), strict=True))
    form = form_class(user=main_user, today=TODAY, data=data)

    assert form.is_valid() == valid


def test_typical_year_reversed_range_is_rejected_not_swapped(main_user):
    # both years hold records, so the only thing wrong is their order — and it
    # is reported as such rather than quietly corrected
    DrinkFactory(date=date(2000, 1, 1))
    DrinkFactory(date=date(2003, 1, 1))

    form = TypicalYearForm(
        user=main_user, today=TODAY, data={"year_from": 2003, "year_to": 2000}
    )

    assert not form.is_valid()
    assert form.errors["year_from"] == [_("Years must be in order")]
    assert "year_to" not in form.errors


def test_drink_filter_opens_on_the_header_year(main_user):
    """The boxes follow the year in the header, not the calendar year."""
    main_user.year = 2000

    form = DrinkCompareForm(user=main_user, today=TODAY).as_p()

    assert '<input type="number" name="year2" value="2000"' in form


@pytest.mark.parametrize(
    "form_class, data, errors",
    [
        pytest.param(
            TypicalYearForm,
            {"year_from": 2014, "year_to": 2015},
            {"year_from": ["2014 metais įrašų nėra."], "year_to": []},
            id="typical_year",
        ),
        pytest.param(
            DrinkCompareForm,
            {"year1": 2014, "year2": 2015},
            {"year1": ["2014 metais įrašų nėra."], "year2": []},
            id="compare",
        ),
    ],
)
def test_a_year_with_no_records_names_itself(main_user, form_class, data, errors):
    DrinkFactory(date=date(2015, 1, 1))

    form = form_class(user=main_user, today=TODAY, data=data)
    form.is_valid()

    assert {field: form.errors.get(field, []) for field in errors} == errors
