from datetime import date

import pytest
import time_machine

from ..forms import BookForm, BookTargetForm
from .factories import BookTargetFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("form_class", "inputs"),
    [
        (
            BookForm,
            [
                '<input type="text" name="started"',
                '<input type="text" name="ended"',
                '<input type="text" name="author"',
                '<input type="text" name="title"',
            ],
        ),
        (
            BookTargetForm,
            ['<input type="text" name="year"', '<input type="number" name="quantity"'],
        ),
    ],
    ids=["book", "book_target"],
)
def test_form_init_fields(main_user, form_class, inputs):
    form = form_class(user=main_user).as_p()

    for expected in inputs:
        assert expected in form
    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
@pytest.mark.parametrize(
    ("form_class", "expected"),
    [
        (BookForm, '<input type="text" name="started" value="1999-01-01"'),
        (BookTargetForm, '<input type="text" name="year" value="1999"'),
    ],
    ids=["book_year", "book_target_year"],
)
def test_form_year_initial_value(main_user, form_class, expected):
    form = form_class(user=main_user).as_p()

    assert expected in form


@pytest.mark.parametrize(
    "ended",
    ["1999-01-31", "1999-01-01"],
    ids=["ended_after_started", "ended_on_started"],
)
def test_book_valid_data(main_user, ended):
    form = BookForm(
        user=main_user,
        data={
            "started": "1999-01-01",
            "ended": ended,
            "author": "Author",
            "title": "Title",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.started == date(1999, 1, 1)
    assert data.ended == date.fromisoformat(ended)
    assert data.author == "Author"
    assert data.title == "Title"
    assert data.user.username == "bob"


@time_machine.travel("2000-2-2")
@pytest.mark.parametrize(
    ("data", "field", "message"),
    [
        ({"started": "1998-1-1"}, "started", "Metai turi būti tarp 1999 ir 2000"),
        ({"started": "2001-1-1"}, "started", "Metai turi būti tarp 1999 ir 2000"),
        ({"started": "2000-2-3"}, "started", "Data negali būti ateityje"),
        (
            {"started": "1999-1-1", "ended": "2000-2-3"},
            "ended",
            "Data negali būti ateityje",
        ),
        (
            {"started": "1999-1-2", "ended": "1999-1-1"},
            "ended",
            "Baigta skaityti negali būti anksčiau nei pradėta skaityti.",
        ),
    ],
    ids=[
        "invalid_start_year_1998",
        "invalid_start_year_2001",
        "invalid_start_date",
        "invalid_end_date",
        "end_date_earlier_than_start_date",
    ],
)
def test_book_refuses_a_date(main_user, data, field, message):
    form = BookForm(user=main_user, data={"author": "Author", "title": "Title", **data})

    assert not form.is_valid()
    assert message in form.errors[field]


@pytest.mark.parametrize(
    ("form_class", "fields"),
    [
        (BookForm, ["started", "author", "title"]),
        (BookTargetForm, ["year", "quantity"]),
    ],
    ids=["book", "book_target"],
)
def test_blank_data(main_user, form_class, fields):
    form = form_class(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == len(fields)
    for field in fields:
        assert field in form.errors


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("author", "Author" * 250),
        ("title", "Title" * 254),
        ("author", "AA"),
        ("title", "T"),
    ],
    ids=["author_too_long", "title_too_long", "author_too_short", "title_too_short"],
)
def test_book_refuses_a_text_out_of_length(main_user, field, value):
    data = {
        "started": "1999-01-01",
        "ended": "1999-01-31",
        "author": "Author",
        "title": "Title",
        field: value,
    }

    form = BookForm(user=main_user, data=data)

    assert not form.is_valid()

    assert field in form.errors


@pytest.mark.parametrize("year", ["2000", 2000], ids=["text", "number"])
def test_book_target_valid_data(year, main_user):
    form = BookTargetForm(user=main_user, data={"year": year, "quantity": 1.0})

    assert form.is_valid()

    data = form.save()

    assert data.year == 2000
    assert data.quantity == 1.0
    assert data.user.username == "bob"


def test_book_target_year_validation(main_user):
    BookTargetFactory()

    form = BookTargetForm(user=main_user, data={"year": 1999, "quantity": 200})

    assert not form.is_valid()

    assert "year" in form.errors
