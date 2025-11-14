from datetime import date
from types import SimpleNamespace

import pytest

from ..factories import BookFactory, BookTargetFactory
from ..services.chart_readed import ChartReaded, ChartReadedData

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                       ChartReadedData
# -------------------------------------------------------------------------------------
def test_data_targets_no_data(main_user):
    actual = ChartReadedData(main_user).targets

    assert actual == {}


def test_data_targets(main_user):
    BookTargetFactory(year=1, quantity=10)
    BookTargetFactory(year=2, quantity=20)

    actual = ChartReadedData(main_user).targets

    assert actual == {1: 10, 2: 20}


def test_data_readed_no_data(main_user):
    actual = ChartReadedData(main_user).readed

    assert actual == {}


def test_data_readed(main_user):
    BookFactory(started=date(2000, 1, 1))
    BookFactory(started=date(2000, 1, 1), ended=date(2000, 1, 31))
    BookFactory(started=date(2000, 1, 1), ended=date(2000, 1, 31))
    BookFactory(started=date(1998, 1, 1))
    BookFactory(started=date(1998, 1, 1), ended=date(1998, 1, 31))

    actual = ChartReadedData(main_user).readed

    assert actual == {1998: 1, 2000: 2}


# -------------------------------------------------------------------------------------
#                                                                           ChartReaded
# -------------------------------------------------------------------------------------
@pytest.fixture(name="readed")
def fixture_readed():
    return {1111: 1, 2222: 2, 3333: 3}


@pytest.fixture(name="targets")
def fixture_targets():
    return {1111: 11, 3333: 33}


def test_chart_context():
    data = SimpleNamespace(readed={}, targets={})

    actual = ChartReaded(data).context()

    assert "categories" in actual
    assert "data" in actual
    assert "targets" in actual
    assert "chart_title" in actual
    assert "chart_column_color" in actual


def test_chart_context_categories(readed, targets):
    data = SimpleNamespace(readed=readed, targets=targets)

    actual = ChartReaded(data).context()
    actual = actual["categories"]

    assert actual == [1111, 2222, 3333]


def test_chart_context_targets(readed, targets):
    data = SimpleNamespace(readed=readed, targets=targets)

    actual = ChartReaded(data).context()
    actual = actual["targets"]

    assert actual == [11, 0, 33]


def test_chart_context_data(readed, targets):
    data = SimpleNamespace(readed=readed, targets=targets)

    actual = ChartReaded(data).context()

    assert actual["data"] == [
        {"y": 1, "target": 11},
        {"y": 2, "target": 0},
        {"y": 3, "target": 33},
    ]


def test_chart_context_chart_title(readed, targets):
    data = SimpleNamespace(readed=readed, targets=targets)

    actual = ChartReaded(data).context()

    assert actual["chart_title"] == "Perskaitytos knygos"
