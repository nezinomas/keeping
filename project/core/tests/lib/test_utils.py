from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import Resolver404
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib import utils

_PROFIT_FIELDS = ["incomes", "fee", "market_value", "profit_sum", "profit_proc"]


@pytest.mark.parametrize(
    "data, fields, expect",
    [
        pytest.param(
            [SimpleNamespace(x=111, A=1, B=2), SimpleNamespace(x=222, A=1, B=2)],
            ["A", "B"],
            {"A": 2, "B": 4},
            id="sums_only_the_named_fields",
        ),
        pytest.param([], ["A", "B"], {"A": 0, "B": 0}, id="zero_without_rows"),
        pytest.param(
            [
                SimpleNamespace(incomes=100, sold=0, profit_sum=200),
                SimpleNamespace(incomes=50, sold=100, profit_sum=100),
            ],
            ["incomes", "profit_sum", "sold"],
            {"incomes": 150, "profit_sum": 300, "sold": 100},
            id="a_zero_adds_nothing",
        ),
    ],
)
def test_total_row_sums_each_field(data, fields, expect):
    assert utils.total_row(data, fields=fields) == expect


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


def _fund_row(shows_profit, **values):
    return SimpleNamespace(shows_profit=shows_profit, **values)


def test_funds_total_row_profit_reads_only_the_rows_that_show_one():
    data = [
        _fund_row(True, incomes=100000, fee=0, market_value=110000, profit_sum=10000),
        _fund_row(False, incomes=50000, fee=0, market_value=0, profit_sum=-30000),
    ]

    actual = utils.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_sum"] == 10000
    assert actual["profit_proc"] == 10.0


def test_funds_total_row_other_cells_stay_the_column_sum():
    data = [
        _fund_row(True, incomes=100000, fee=5, market_value=110000, profit_sum=10000),
        _fund_row(False, incomes=50000, fee=7, market_value=20000, profit_sum=-30000),
    ]

    actual = utils.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["incomes"] == 150000
    assert actual["fee"] == 12
    assert actual["market_value"] == 130000


def test_funds_total_row_takes_the_switched_money_off_the_shown_base():
    data = [
        _fund_row(True, incomes=230000, fee=0, market_value=140000, profit_sum=10000),
    ]

    actual = utils.funds_total_row(data, fields=_PROFIT_FIELDS, switched_within=100000)

    assert actual["profit_proc"] == pytest.approx(10000 / 130000 * 100)


@pytest.mark.parametrize("switched_within", [100000, 150000])
def test_funds_total_row_profit_is_zero_when_the_base_is_used_up(switched_within):
    data = [_fund_row(True, incomes=100000, fee=0, market_value=0, profit_sum=30000)]

    actual = utils.funds_total_row(
        data, fields=_PROFIT_FIELDS, switched_within=switched_within
    )

    assert actual["profit_proc"] == 0.0


def test_funds_total_row_no_row_shows_a_profit():
    data = [_fund_row(False, incomes=50000, fee=0, market_value=0, profit_sum=-3)]

    actual = utils.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_sum"] == 0
    assert actual["profit_proc"] == 0
