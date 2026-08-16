import re
from datetime import date, datetime

import pytest
import time_machine
from django.conf import settings
from django.urls import resolve, reverse

from ...core.lib.day_stats import Stats
from ...core.lib.stat_card import EMPTY
from .. import views
from .factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db


def _context(client_logged):
    url = reverse("counts:tab_periodicity", kwargs={"slug": "count-type"})
    return client_logged.get(url).context


def _script_keys() -> set[str]:
    source = (
        settings.SITE_ROOT / "static" / "js" / "chart_counts_periodicity.js"
    ).read_text(encoding="utf-8")

    return set(re.findall(r"chartData\.(\w+)", source))


def test_periodicity_func():
    view = resolve("/counts/xxx/periodicity/")

    assert views.TabPeriodicity is view.func.view_class


def test_periodicity_200(client_logged):
    CountTypeFactory()

    url = reverse("counts:tab_periodicity", kwargs={"slug": "count-type"})

    assert client_logged.get(url).status_code == 200


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


def test_periodicity_carries_the_three_charts(client_logged):
    CountTypeFactory()

    context = _context(client_logged)

    assert "chart_weekdays" in context
    assert "chart_months" in context
    assert "chart_histogram" in context
    assert "chart_years" not in context


def test_periodicity_weekdays_are_monday_first_and_lithuanian(client_logged):
    CountFactory()

    categories = _context(client_logged)["chart_weekdays"]["categories"]

    assert categories == [name[:4] for name in Stats.weekdays()]
    assert len(categories) == 7
    assert categories[0] == "Pirm"


def test_periodicity_months_are_twelve(client_logged):
    CountFactory()

    assert len(_context(client_logged)["chart_months"]["categories"]) == 12


def test_periodicity_charts_pool_every_record_and_caption_the_span(client_logged):
    CountFactory(date=date(1996, 5, 1))
    CountFactory(date=date(1999, 1, 1))

    context = _context(client_logged)

    assert sum(context["chart_weekdays"]["data"]) == 2
    for key in ("chart_weekdays", "chart_months", "chart_histogram"):
        assert context[key]["subtitle"] == "1996–1999"


def test_periodicity_charts_of_a_single_year_caption_that_year_alone(client_logged):
    CountFactory(date=date(1999, 1, 1))

    assert _context(client_logged)["chart_weekdays"]["subtitle"] == "1999"


def test_periodicity_charts_are_titled_under_the_key_the_script_reads(client_logged):
    CountFactory()

    assert "chart_title" in _script_keys()
    assert _context(client_logged)["chart_weekdays"]["chart_title"] == "Savaitės dienos"


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
