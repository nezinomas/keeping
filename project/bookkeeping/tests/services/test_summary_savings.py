import factory
import pytest
import time_machine
from django.db.models.signals import post_save
from hypothesis import given, settings
from hypothesis import strategies as st

from ....savings.services.model_services import SavingBalanceModelService
from ....savings.tests.factories import SavingBalanceFactory
from ...services.summary_savings import chart_keys_map, load_service, make_chart


@pytest.fixture(name="data1")
def fixture_data1():
    return [
        {"year": 1999, "incomes": 0, "profit": 0, "total": 0},
        {"year": 2000, "incomes": 1, "profit": 1, "total": 2},
        {"year": 2001, "incomes": 2, "profit": 2, "total": 4},
    ]


@pytest.fixture(name="data2")
def fixture_data2():
    return [
        {"year": 1999, "incomes": 0, "profit": 0, "total": 0},
        {"year": 2000, "incomes": 4, "profit": 4, "total": 8},
        {"year": 2001, "incomes": 5, "profit": 5, "total": 10},
    ]


@pytest.fixture(name="load_data_full")
def fixture_load_data_full(data1, data2):
    return {
        "funds": data1,
        "shares": data2,
        "pensions2": data1,
        "pensions": data2,
    }


@pytest.fixture(name="load_data_funds")
def fixture_load_data_funds(data1):
    return {
        "funds": data1,
        "shares": [],
        "pensions2": [],
        "pensions": [],
    }


int_stragegy = st.integers()
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


@settings(max_examples=30)
@given(data_stragety)
def test_chart_data_with_hypothesis(data):
    make_chart("x", data)


def test_chart_data_1(data1):
    actual = make_chart("x", data1)

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


@time_machine.travel("2000-1-1")
def test_chart_data_2(data1):
    actual = make_chart("x", data1)

    assert actual["categories"] == [2000]
    assert actual["invested"] == [1]
    assert actual["profit"] == [1]
    assert actual["total"] == [2]


def test_chart_data_3(data1, data2):
    actual = make_chart("x", data1, data2)

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [5, 7]
    assert actual["profit"] == [5, 7]
    assert actual["total"] == [10, 14]


@time_machine.travel("2000-1-1")
def test_chart_data_4(data1, data2):
    actual = make_chart("x", data1, data2)

    assert actual["categories"] == [2000]
    assert actual["invested"] == [5]
    assert actual["profit"] == [5]
    assert actual["total"] == [10]


def test_chart_data_5(data1):
    actual = make_chart("x", data1, [])

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


def test_chart_data_6():
    actual = make_chart("x", [])

    assert not actual["categories"]
    assert not actual["invested"]
    assert not actual["profit"]
    assert not actual["total"]


def test_chart_keeps_a_year_whose_shown_rows_paid_nothing_in():
    actual = make_chart(
        "x", [{"year": 1999, "incomes": 0, "profit": 37000, "total": 37000}]
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

    actual = make_chart("x", list(qs.filter(type="funds")))

    assert actual["categories"] == [2000, 2001]
    assert actual["invested"] == [1, 2]
    assert actual["profit"] == [1, 2]
    assert actual["total"] == [2, 4]


def test_load_service_requires_the_chart_keys(load_data_full):
    with pytest.raises(TypeError):
        load_service(load_data_full)  # pylint: disable=no-value-for-parameter


def test_load_service_records_full(load_data_full):
    actual = load_service(load_data_full, chart_keys_map())
    expect = 12

    assert actual["records"] == expect


def test_load_service_records_funds(load_data_funds):
    actual = load_service(load_data_funds, chart_keys_map())
    expect = 6

    assert actual["records"] == expect


def test_load_service_template_variables_full(load_data_full):
    actual = load_service(load_data_full, chart_keys_map())
    expect = [
        "funds",
        "shares",
        "funds_shares",
        "pensions",
        "pensions2",
        "funds_shares_pensions",
    ]

    assert actual["pointers"] == expect
    assert list(actual["charts"].keys()) == expect


def test_load_service_template_variables_funds(load_data_funds):
    actual = load_service(load_data_funds, chart_keys_map())
    expect = [
        "funds",
        "funds_shares",
        "funds_shares_pensions",
    ]

    assert actual["pointers"] == expect
    assert list(actual["charts"].keys()) == expect


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
@settings(max_examples=30)
@factory.django.mute_signals(post_save)
def test_load_service_with_hypothesis(data):
    load_service(data, chart_keys_map())
