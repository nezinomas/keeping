from datetime import date

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ....savings.services.model_services import SavingBalanceModelService
from ....savings.tests.factories import SavingBalanceFactory
from ...services.summary_savings import chart_keys_map, load_service, make_chart

DATA1 = [
    {"year": 1999, "incomes": 0, "profit": 0, "total": 0},
    {"year": 2000, "incomes": 1, "profit": 1, "total": 2},
    {"year": 2001, "incomes": 2, "profit": 2, "total": 4},
]
DATA2 = [
    {"year": 1999, "incomes": 0, "profit": 0, "total": 0},
    {"year": 2000, "incomes": 4, "profit": 4, "total": 8},
    {"year": 2001, "incomes": 5, "profit": 5, "total": 10},
]
LOAD_FULL = {"funds": DATA1, "shares": DATA2, "pensions2": DATA1, "pensions": DATA2}
LOAD_FUNDS = {"funds": DATA1, "shares": [], "pensions2": [], "pensions": []}
TODAY = date(2010, 1, 1)


data_stragety = st.lists(
    st.fixed_dictionaries(
        {
            "year": st.integers(min_value=1974, max_value=2050),
            "incomes": st.integers(min_value=0, max_value=1_000_000),
            "profit": st.integers(min_value=-1_000, max_value=1_000),
            "total": st.integers(min_value=0, max_value=1_000_000),
        }
    ),
    max_size=15,
)


@given(data_stragety)
@example(data=[{"year": 1999, "incomes": 0, "profit": 500, "total": 0}])
def test_chart_data_with_hypothesis(data):
    actual = make_chart("x", data, today=TODAY)

    years = actual["categories"]
    assert years == sorted(set(years))
    assert all(year <= TODAY.year for year in years)
    assert len(actual["invested"]) == len(years)
    assert len(actual["profit"]) == len(years)
    assert len(actual["total"]) == len(years)
    assert len(actual["proc"]) == len(years)
    for year, total in zip(years, actual["total"], strict=True):
        assert total == sum(row["total"] for row in data if row["year"] == year)
    past = {row["year"] for row in data if row["year"] <= TODAY.year}
    expected = {
        year
        for year in past
        if sum(row["total"] for row in data if row["year"] == year)
        or sum(row["profit"] for row in data if row["year"] == year)
    }
    assert expected <= set(years)


@pytest.mark.parametrize(
    "today, sources, categories, invested, profit, total",
    [
        pytest.param(TODAY, [DATA1], [2000, 2001], [1, 2], [1, 2], [2, 4], id="one"),
        pytest.param(
            date(2000, 1, 1), [DATA1], [2000], [1], [1], [2], id="one_year_cut"
        ),
        pytest.param(
            TODAY, [DATA1, DATA2], [2000, 2001], [5, 7], [5, 7], [10, 14], id="two"
        ),
        pytest.param(
            date(2000, 1, 1), [DATA1, DATA2], [2000], [5], [5], [10], id="two_year_cut"
        ),
        pytest.param(
            TODAY,
            [DATA1, []],
            [2000, 2001],
            [1, 2],
            [1, 2],
            [2, 4],
            id="empty_second",
        ),
        pytest.param(TODAY, [[]], [], [], [], [], id="no_data"),
    ],
)
def test_chart_data(today, sources, categories, invested, profit, total):
    actual = make_chart("x", *sources, today=today)

    assert actual["categories"] == categories
    assert actual["invested"] == invested
    assert actual["profit"] == profit
    assert actual["total"] == total


def test_chart_keeps_a_year_whose_shown_rows_paid_nothing_in():
    actual = make_chart(
        "x",
        [{"year": 1999, "incomes": 0, "profit": 37000, "total": 37000}],
        today=TODAY,
    )

    assert actual["categories"] == [1999]
    assert actual["total"] == [37000]
    assert actual["proc"] == [0.0]


@pytest.mark.django_db
def test_chart_data_db1(main_user):
    SavingBalanceFactory(year=1999, incomes=0, profit_sum=0, market_value=0)
    SavingBalanceFactory(year=2000, incomes=1, profit_sum=1, market_value=2)
    SavingBalanceFactory(year=2001, incomes=2, profit_sum=2, market_value=4)

    qs = SavingBalanceModelService(main_user).sum_by_type()

    actual = make_chart("x", list(qs.filter(type="funds")), today=TODAY)

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


@pytest.mark.parametrize(
    "data, expect",
    [
        pytest.param(LOAD_FULL, 12, id="full"),
        pytest.param(LOAD_FUNDS, 6, id="funds"),
    ],
)
def test_load_service_records(data, expect):
    actual = load_service(data, chart_keys_map(), TODAY)

    assert actual["records"] == expect


@pytest.mark.parametrize(
    "data, expect, titles",
    [
        pytest.param(
            LOAD_FULL,
            [
                "funds",
                "shares",
                "funds_shares",
                "pensions",
                "pensions2",
                "funds_shares_pensions",
            ],
            [
                "Fondai",
                "Akcijos",
                "Fondai, Akcijos",
                "Pensijos III",
                "Pensijos II",
                "Fondai, Akcijos, Pensijos III",
            ],
            id="full",
        ),
        pytest.param(
            LOAD_FUNDS,
            ["funds", "funds_shares", "funds_shares_pensions"],
            ["Fondai", "Fondai, Akcijos", "Fondai, Akcijos, Pensijos III"],
            id="funds",
        ),
    ],
)
def test_load_service_template_variables(data, expect, titles):
    actual = load_service(data, chart_keys_map(), TODAY)

    assert actual["pointers"] == expect
    assert list(actual["charts"].keys()) == expect
    assert [chart["title"] for chart in actual["charts"].values()] == titles


@given(
    st.fixed_dictionaries(
        {
            "funds": data_stragety,
            "shares": data_stragety,
            "pensions": data_stragety,
            "pensions2": data_stragety,
        }
    )
)
def test_load_service_with_hypothesis(data):
    actual = load_service(data, chart_keys_map(), TODAY)

    assert actual["records"] == sum(
        len(chart["categories"]) for chart in actual["charts"].values()
    )
    assert all(chart["categories"] for chart in actual["charts"].values())
