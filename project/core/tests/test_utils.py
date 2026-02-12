from types import SimpleNamespace

from django.test import override_settings
from django.urls import Resolver404

from ..lib import utils


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

    assert actual == {"incomes": 100, "profit_sum": 200, "sold": 100}


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
