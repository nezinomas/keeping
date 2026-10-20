from datetime import date

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...services.month_filter import FilterItem, MonthFilter

# no example below asks for July, so a fallback that reads the clock cannot pass
TODAY = date(1999, 7, 15)
URL_VALUES = (*(str(month) for month in range(1, 13)), "all")


@given(st.sampled_from(URL_VALUES))
@example("1")
@example("12")
@example("all")
def test_a_month_or_all_round_trips_through_its_url(value):
    assert MonthFilter.parse(value, TODAY).value == value


@given(st.text().filter(lambda value: value not in (*URL_VALUES, "13")))
@example("junk")
@example("0")
@example("")
def test_anything_else_falls_back_to_todays_month(value):
    assert MonthFilter.parse(value, TODAY) == MonthFilter("7")


def test_the_old_routes_13_lists_every_month():
    assert MonthFilter.parse("13", TODAY) == MonthFilter("all")


def test_the_items_name_every_month_then_all_and_mark_the_open_one():
    labels = [
        "Sausis",
        "Vasaris",
        "Kovas",
        "Balandis",
        "Gegužė",
        "Birželis",
        "Liepa",
        "Rugpjūtis",
        "Rugsėjis",
        "Spalis",
        "Lapkritis",
        "Gruodis",
        "Visi įrašai",
    ]

    actual = MonthFilter("3").items("/t/")

    assert actual == [
        FilterItem(label, f"/t/?month={value}", value == "3")
        for label, value in zip(labels, URL_VALUES, strict=True)
    ]


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("all", {}, id="all"),
        pytest.param("3", {"date__month": 3}, id="month"),
    ],
)
def test_a_filter_looks_its_month_up_in_the_date(value, expected):
    assert MonthFilter(value).lookup() == expected
