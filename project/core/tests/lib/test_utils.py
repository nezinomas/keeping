from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import Resolver404

from ...lib import utils

_PROFIT_FIELDS = ["incomes", "fee", "market_value", "profit_sum", "profit_proc"]


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

    assert actual == {"incomes": 150, "profit_sum": 300, "sold": 100}


def test_total_row_profit_proc_with_sold_row():
    data = [
        SimpleNamespace(
            incomes=1000, fee=10, sold=0, market_value=1200, profit_sum=190
        ),
        SimpleNamespace(
            incomes=2596753,
            fee=20000,
            sold=3459722,
            market_value=500,
            profit_sum=843469,
        ),
    ]

    actual = utils.total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_proc"] == pytest.approx(843659 / 2597753 * 100)


def test_total_row_profit_proc_closed_rows_only():
    data = [
        SimpleNamespace(
            incomes=2596753,
            fee=20000,
            sold=3459722,
            market_value=0,
            profit_sum=842969,
            profit_proc=32.46,
        ),
        SimpleNamespace(
            incomes=10600,
            fee=0,
            sold=3656,
            market_value=0,
            profit_sum=-6944,
            profit_proc=-65.51,
        ),
    ]

    actual = utils.total_row(data, fields=_PROFIT_FIELDS)

    assert actual["market_value"] == 0
    assert actual["profit_proc"] == pytest.approx(836025 / 2607353 * 100)


def test_total_row_profit_proc_no_incomes():
    data = [SimpleNamespace(incomes=0, fee=0, market_value=50, profit_sum=50)]

    actual = utils.total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_proc"] == 0


def test_get_safe_redirect_no_url(rf):
    """Should return fallback if URL is None/empty."""
    request = rf.get("/")
    assert utils.get_safe_redirect(request, None) == "/"


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_unsafe_host(rf):
    """Should return fallback if the host is not allowed."""
    request = rf.get("/", HTTP_HOST="mysite.com")
    # Malicious external domain
    unsafe_url = "https://evil.com/dashboard"
    assert utils.get_safe_redirect(request, unsafe_url) == "/"


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_invalid_path(rf, mocker):
    """Should return fallback if path does not exist in URLconf."""
    request = rf.get("/", HTTP_HOST="mysite.com")
    safe_host_url = "https://mysite.com/fake-page"

    # Mock resolve to raise Resolver404
    mocker.patch("project.core.lib.utils.resolve", side_effect=Resolver404)

    assert utils.get_safe_redirect(request, safe_host_url) == "/"


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_success(rf, mocker):
    """Should return path if URL is safe and exists."""
    request = rf.get("/", HTTP_HOST="mysite.com")
    valid_url = "https://mysite.com/settings/year"

    # Mock resolve to succeed (return any truthy object)
    mocker.patch("project.core.lib.utils.resolve", return_value=True)

    assert utils.get_safe_redirect(request, valid_url) == "/settings/year"


def test_get_safe_redirect_custom_fallback(rf):
    """Should return custom fallback if validation fails."""
    request = rf.get("/")
    assert utils.get_safe_redirect(request, None, fallback="/dashboard") == "/dashboard"


def test_add_fast_urls_basic(mocker):
    # Patch the reference inside your specific utils file!
    mock_reverse = mocker.patch("project.core.lib.utils.reverse")

    def side_effect(viewname, args):
        app_action = viewname.replace(":", "/")
        return f"/{app_action}/{args[0]}/"

    mock_reverse.side_effect = side_effect

    raw_data = [
        {"id": 1, "title": "Coffee"},
        {"id": 99, "title": "Laptop"},
    ]

    actual = utils.add_fast_urls(data=raw_data, app_name="expenses")

    assert len(actual) == 2
    assert actual[0]["url_update"] == "/expenses/update/1/"
    assert actual[0]["url_delete"] == "/expenses/delete/1/"
    assert actual[1]["url_update"] == "/expenses/update/99/"
    assert actual[1]["url_delete"] == "/expenses/delete/99/"


def test_add_fast_urls_custom_pk_key(mocker):
    # Patch the reference inside your specific utils file!
    mock_reverse = mocker.patch("project.core.lib.utils.reverse")

    # Use side_effect here too, since reverse is called twice (update & delete)
    def side_effect(viewname, args):
        app_action = viewname.replace(":", "/")
        return f"/{app_action}/{args[0]}/"

    mock_reverse.side_effect = side_effect

    raw_data = [{"custom_pk": 42}]

    actual = utils.add_fast_urls(data=raw_data, app_name="app", pk_key="custom_pk")

    assert actual[0]["url_update"] == "/app/update/42/"
    assert actual[0]["url_delete"] == "/app/delete/42/"


def test_http_htmx_response_trigger_detail_is_an_object():
    """htmx 4 throws on a null event detail - the header must carry {}."""
    response = utils.http_htmx_response("reload")

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


def test_http_htmx_response_without_trigger():
    response = utils.http_htmx_response()

    assert response.status_code == 204
    assert "HX-Trigger" not in response.headers


@pytest.mark.parametrize(
    "value, expected",
    [("7", 7), (7, 7), ("-3", -3), (None, 0), ("", 0), ("abc", 0), ("1.5", 0)],
)
def test_int_or_zero(value, expected):
    assert utils.int_or_zero(value) == expected
