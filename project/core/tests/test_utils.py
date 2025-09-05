from types import SimpleNamespace

from mock import patch

from ..lib import utils


@patch("project.core.lib.utils.CrequestMiddleware")
def test_get_request_kwargs(mck):
    mck.get_request.return_value = SimpleNamespace(
        resolver_match=SimpleNamespace(kwargs={"Foo": "Boo"})
    )
    actual = utils.get_request_kwargs("Foo")
    assert actual == "Boo"


@patch("project.core.lib.utils.CrequestMiddleware")
def test_get_request_kwargs_no_name(mck):
    mck.get_request.return_value = SimpleNamespace(
        resolver_match=SimpleNamespace(kwargs={})
    )
    actual = utils.get_request_kwargs("Foo")
    assert not actual


def test_total_row_objects():
    data = [
        SimpleNamespace(x=111, A=1, B=2),
        SimpleNamespace(x=222, A=1, B=2),
    ]
    actual = utils.total_row(data, fields=["A", "B"])

    assert actual == {
        "A": 2,
        "B": 4,
    }


def test_total_row_no_data():
    actual = utils.total_row([], fields=["A", "B"])

    assert actual == {
        "A": 0,
        "B": 0,
    }


def test_total_row_with_sold():
    data = [
        SimpleNamespace(incomes=100, sold=0, profit_sum=200),
        SimpleNamespace(incomes=50, sold=100, profit_sum=100),
    ]

    actual = utils.total_row(data, fields=["incomes", "profit_sum", "sold"])

    assert actual == {'incomes': 100, 'profit_sum': 200, 'sold': 100}

