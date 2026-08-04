from datetime import date
from types import SimpleNamespace

import pytest

from ...services.chart_finished import ChartFinished, ChartFinishedData
from ..factories import BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                     ChartFinishedData
# -------------------------------------------------------------------------------------
def test_data_targets_no_data(main_user):
    actual = ChartFinishedData(main_user).targets

    assert actual == {}


def test_data_targets(main_user):
    BookTargetFactory(year=1, quantity=10)
    BookTargetFactory(year=2, quantity=20)

    actual = ChartFinishedData(main_user).targets

    assert actual == {1: 10, 2: 20}


def test_data_finished_no_data(main_user):
    actual = ChartFinishedData(main_user).finished

    assert actual == {}


def test_data_finished(main_user):
    BookFactory(started=date(2000, 1, 1))
    BookFactory(started=date(2000, 1, 1), ended=date(2000, 1, 31))
    BookFactory(started=date(2000, 1, 1), ended=date(2000, 1, 31))
    BookFactory(started=date(1998, 1, 1))
    BookFactory(started=date(1998, 1, 1), ended=date(1998, 1, 31))

    actual = ChartFinishedData(main_user).finished

    assert actual == {1998: 1, 2000: 2}


# -------------------------------------------------------------------------------------
#                                                                         ChartFinished
# -------------------------------------------------------------------------------------
@pytest.fixture(name="finished")
def fixture_finished():
    return {1111: 1, 2222: 2, 3333: 3}


@pytest.fixture(name="targets")
def fixture_targets():
    return {1111: 11, 3333: 33}


def test_chart_context():
    data = SimpleNamespace(finished={}, targets={})

    actual = ChartFinished(data).context()

    assert "categories" in actual
    assert "data" in actual
    assert "targets" in actual
    assert "chart_title" in actual
    assert "chart_column_color" in actual


def test_chart_context_categories(finished, targets):
    data = SimpleNamespace(finished=finished, targets=targets)

    actual = ChartFinished(data).context()
    actual = actual["categories"]

    assert actual == [1111, 2222, 3333]


def test_chart_context_targets(finished, targets):
    data = SimpleNamespace(finished=finished, targets=targets)

    actual = ChartFinished(data).context()
    actual = actual["targets"]

    assert actual == [11, 0, 33]


def test_chart_context_data(finished, targets):
    data = SimpleNamespace(finished=finished, targets=targets)

    actual = ChartFinished(data).context()

    assert actual["data"] == [
        {"y": 1, "target": 11},
        {"y": 2, "target": 0},
        {"y": 3, "target": 33},
    ]


def test_chart_context_chart_title(finished, targets):
    data = SimpleNamespace(finished=finished, targets=targets)

    actual = ChartFinished(data).context()

    assert actual["chart_title"] == "Perskaitytos knygos"
