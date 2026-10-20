import re
from datetime import date, datetime, timedelta

import pytest
import time_machine
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.dates import WEEKDAYS_ABBR

from ...core.lib.stat_card import EMPTY
from .factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db


def _response(client_logged):
    url = reverse("counts:tab_periodicity", kwargs={"slug": "count-type"})
    return client_logged.get(url)


def _context(client_logged):
    return _response(client_logged).context


def _script_keys() -> set[str]:
    source = (
        settings.SITE_ROOT / "static" / "js" / "chart_counts_periodicity.js"
    ).read_text(encoding="utf-8")

    return set(re.findall(r"chartData\.(\w+)", source))


def test_periodicity_is_the_second_tab(client_logged):
    CountTypeFactory()

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    content = client_logged.get(url).content.decode("utf-8")

    assert content.index("Periodiškumas") < content.index("Istorija")


@time_machine.travel(datetime(1999, 7, 12))
def test_periodicity_has_three_cards_in_order(client_logged):
    CountTypeFactory()

    assert [card.title for card in _context(client_logged)["cards"]] == [
        "Per metus",
        "Vidutinis tarpas",
        "Ilgiausias tarpas",
    ]


@time_machine.travel(datetime(1999, 7, 12))
def test_periodicity_cards_state_the_lifetime_and_note_the_year(client_logged):
    CountFactory(date=date(1997, 1, 1))
    CountFactory(date=date(1997, 3, 1))
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 2, 1))

    rate, median, longest = _context(client_logged)["cards"]

    assert rate.value == "1,9"
    assert rate.note == "šiemet: 2"
    assert median.value == "59"
    assert median.note == "šiemet: 351 d."
    assert longest.value == "671"
    assert longest.note == "1997-03-01 → 1999-01-01"


@time_machine.travel(datetime(1999, 7, 12))
def test_periodicity_cards_explain_which_median_and_which_denominator(client_logged):
    CountFactory(date=date(1997, 1, 1))
    CountFactory(date=date(1999, 1, 1))

    rate, median, longest = _context(client_logged)["cards"]

    assert rate.explanation == ("Vidutiniškai įrašų per metus, per visą laiką",)
    assert median.explanation == ("Visų tarpų mediana",)
    assert longest.explanation == ()


@time_machine.travel(datetime(1999, 7, 12))
def test_periodicity_of_a_counter_with_no_records_is_empty(client_logged):
    CountTypeFactory()

    assert [card.state for card in _context(client_logged)["cards"]] == [EMPTY] * 3


def test_periodicity_leaves_the_years_chart_to_history(client_logged):
    CountTypeFactory()

    assert "chart_years" not in _context(client_logged)


def test_periodicity_weekdays_are_monday_first_and_lithuanian(client_logged):
    CountFactory()

    categories = _context(client_logged)["chart_weekdays"]["categories"]

    assert categories == [str(WEEKDAYS_ABBR[day]) for day in range(7)]
    assert len(categories) == 7
    assert len(set(categories)) == 7


def test_periodicity_months_are_twelve(client_logged):
    CountFactory()

    assert len(_context(client_logged)["chart_months"]["categories"]) == 12


def test_periodicity_months_are_the_full_month_names(client_logged):
    CountFactory()

    assert _context(client_logged)["chart_months"]["categories"] == [
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
    ]


def test_periodicity_charts_pool_every_record_and_caption_the_span(client_logged):
    CountFactory(date=date(1996, 5, 1))
    CountFactory(date=date(1999, 1, 1))

    response = _response(client_logged)
    content = response.content.decode("utf-8")

    assert sum(response.context["chart_weekdays"]["data"]) == 2
    assert response.context["span"] == "1996–1999"
    assert content.count('<p class="panel__subtitle">1996–1999</p>') == 3


def test_periodicity_charts_of_a_single_year_caption_that_year_alone(client_logged):
    CountFactory(date=date(1999, 1, 1))

    response = _response(client_logged)

    assert response.context["span"] == "1999"
    assert '<p class="panel__subtitle">1999</p>' in response.content.decode("utf-8")


def test_periodicity_panels_are_titled_in_lithuanian(client_logged):
    CountFactory()

    content = _response(client_logged).content.decode("utf-8")

    assert '<h2 class="panel__title">Savaitės dienos</h2>' in content
    assert '<h2 class="panel__title">Mėnesiai</h2>' in content
    assert '<h2 class="panel__title">Tarpų dažnis, dienomis</h2>' in content


def test_periodicity_gap_distribution_bins_rather_than_drawing_a_bar_a_length(
    client_logged,
):
    day = date(1999, 1, 1)
    CountFactory(date=day)
    for gap in (2, 3, 5, 8, 13, 21, 34, 55, 89, 144):
        day += timedelta(days=gap)
        CountFactory(date=day)

    chart = _context(client_logged)["chart_histogram"]

    assert len(chart["categories"]) <= 8
    assert sum(chart["data"]) == 10
    assert chart["categories"][0].startswith("2")


def test_periodicity_chart_payload_matches_the_keys_its_script_reads(client_logged):
    CountFactory()

    assert _script_keys() == set(_context(client_logged)["chart_weekdays"])


def test_periodicity_renders_its_chart_containers(client_logged):
    CountFactory()

    url = reverse("counts:tab_periodicity", kwargs={"slug": "count-type"})
    content = client_logged.get(url).content.decode("utf-8")

    assert '<div id="chart-weekdays-container"></div>' in content
    assert '<div id="chart-months-container"></div>' in content
    assert '<div id="chart-histogram-container">' in content


def _tab_queries(client, name):
    url = reverse(name, kwargs={"slug": "count-type"})
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


@pytest.mark.parametrize(
    "name", ["counts:index", "counts:tab_periodicity", "counts:tab_history"]
)
def test_tab_query_count_does_not_grow_with_the_records(client_logged, name):
    for _i in range(2):
        CountFactory()
    two = _tab_queries(client_logged, name)

    for _i in range(2, 6):
        CountFactory()
    six = _tab_queries(client_logged, name)

    assert six == two
