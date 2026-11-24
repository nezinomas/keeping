import pytest
from django.test import override_settings
from django.urls import Resolver404
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib import utils


@pytest.mark.parametrize(
    "fallback, expect",
    [
        pytest.param({}, "/", id="the_root"),
        pytest.param({"fallback": "/dashboard"}, "/dashboard", id="the_given_one"),
    ],
)
def test_get_safe_redirect_without_url_returns_the_fallback(rf, fallback, expect):
    assert utils.get_safe_redirect(rf.get("/"), None, **fallback) == expect


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_unsafe_host(rf):
    request = rf.get("/", HTTP_HOST="mysite.com")
    unsafe_url = "https://evil.com/dashboard"
    assert utils.get_safe_redirect(request, unsafe_url) == "/"


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_invalid_path(rf, mocker):
    request = rf.get("/", HTTP_HOST="mysite.com")
    safe_host_url = "https://mysite.com/fake-page"

    mocker.patch("project.core.lib.utils.resolve", side_effect=Resolver404)

    assert utils.get_safe_redirect(request, safe_host_url) == "/"


@override_settings(ALLOWED_HOSTS=["mysite.com"])
def test_get_safe_redirect_success(rf, mocker):
    request = rf.get("/", HTTP_HOST="mysite.com")
    valid_url = "https://mysite.com/settings/year"

    mocker.patch("project.core.lib.utils.resolve", return_value=True)

    assert utils.get_safe_redirect(request, valid_url) == "/settings/year"


@pytest.mark.parametrize(
    "rows, pk_key, expected",
    [
        pytest.param(
            [{"id": 1, "title": "Coffee"}, {"id": 99, "title": "Laptop"}],
            "id",
            [
                ("/v0/app/update/1/", "/v0/app/delete/1/"),
                ("/v0/app/update/99/", "/v0/app/delete/99/"),
            ],
            id="id",
        ),
        pytest.param(
            [{"custom_pk": 42}],
            "custom_pk",
            [("/v0/app/update/42/", "/v0/app/delete/42/")],
            id="custom_pk",
        ),
    ],
)
def test_add_fast_urls_fills_only_the_pk_of_each_url(mocker, rows, pk_key, expected):
    # a 0 outside the pk's place stays: the urls are reversed with a pk of 0
    mocker.patch(
        "project.core.lib.utils.reverse",
        side_effect=lambda name, args: f"/v0/{name.replace(':', '/')}/{args[0]}/",
    )

    actual = utils.add_fast_urls(
        rows, update="app:update", delete="app:delete", pk_key=pk_key
    )

    assert [(row["url_update"], row["url_delete"]) for row in actual] == expected


def test_add_fast_urls_raises_on_a_row_without_the_pk(mocker):
    mocker.patch("project.core.lib.utils.reverse", return_value="/app/update/0/")

    with pytest.raises(KeyError, match="id"):
        utils.add_fast_urls(
            [{"title": "no id"}], update="app:update", delete="app:delete"
        )


def test_http_htmx_response_trigger_detail_is_an_object():
    """htmx 4 throws on a null event detail - the header must carry {}."""
    response = utils.http_htmx_response("reload")

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


def test_http_htmx_response_without_trigger():
    response = utils.http_htmx_response()

    assert response.status_code == 204
    assert "HX-Trigger" not in response.headers


@st.composite
def values_and_ints(draw):
    """An int or its text, read as itself; anything else, read as 0."""
    if draw(st.booleans()):
        number = draw(st.integers())
        return draw(st.sampled_from([number, str(number)])), number

    not_an_int = st.none() | st.text(alphabet="12-x.,").filter(
        lambda text: not text.lstrip("-").isdigit()
    )
    return draw(not_an_int), 0


@given(values_and_ints())
@example(("7", 7))
@example((7, 7))
@example(("-3", -3))
@example((None, 0))
@example(("", 0))
@example(("abc", 0))
@example(("1.5", 0))
def test_int_or_zero(case):
    value, number = case

    assert utils.int_or_zero(value) == number
