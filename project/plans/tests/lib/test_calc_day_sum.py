import polars as pl
import pytest

from ...lib.calc_day_sum import PlanCalculateDaySum


@pytest.fixture(name="data")
def fixture_data():
    obj = type("PlanCollectData", (object,), {})
    obj.incomes = [
        {"month": 1, "amount": 900},
        {"month": 2, "amount": 1000},
        {"month": 3, "amount": 450},
        {"month": 4, "amount": 450},
        {"month": 5, "amount": 450},
        {"month": 6, "amount": 450},
        {"month": 7, "amount": 450},
        {"month": 8, "amount": 450},
        {"month": 9, "amount": 450},
        {"month": 10, "amount": 450},
        {"month": 11, "amount": 450},
        {"month": 12, "amount": 450},
    ]

    obj.expenses_regular = [
        {"month": 1, "amount": 260},
        {"month": 2, "amount": 280},
    ]

    obj.expenses_necessary = [
        {"month": 1, "amount": 300},
        {"month": 2, "amount": 320},
    ]

    obj.savings = [
        {"month": 1, "amount": 190},
        {"month": 2, "amount": 200},
    ]

    obj.per_day = [
        {"month": 1, "amount": 25},
        {"month": 2, "amount": 26},
    ]

    obj.necessary = [
        {"month": 2, "amount": 100},
    ]

    obj.month_len = [
        {"month": 1, "amount": 31},
        {"month": 2, "amount": 29},
        {"month": 3, "amount": 31},
        {"month": 4, "amount": 30},
        {"month": 5, "amount": 31},
        {"month": 6, "amount": 30},
        {"month": 7, "amount": 31},
        {"month": 8, "amount": 31},
        {"month": 9, "amount": 30},
        {"month": 10, "amount": 31},
        {"month": 11, "amount": 30},
        {"month": 12, "amount": 31},
    ]

    return obj


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return type(
        "PlanCollectData",
        (object,),
        {
            "incomes": [],
            "expenses_regular": [],
            "expenses_necessary": [],
            "savings": [],
            "per_day": [],
            "necessary": [],
            "month_len": [
                {"month": 1, "amount": 31},
                {"month": 2, "amount": 29},
                {"month": 3, "amount": 31},
                {"month": 4, "amount": 30},
                {"month": 5, "amount": 31},
                {"month": 6, "amount": 30},
                {"month": 7, "amount": 31},
                {"month": 8, "amount": 31},
                {"month": 9, "amount": 30},
                {"month": 10, "amount": 31},
                {"month": 11, "amount": 30},
                {"month": 12, "amount": 31},
            ],
        },
    )


def test_filter_df_wrong_type(data):
    actual = PlanCalculateDaySum(data).get_row("xxx")

    assert actual == {}


def test_incomes(data):
    actual = PlanCalculateDaySum(data).get_row("incomes")

    assert len(actual) == 12
    assert actual["1"] == 900
    assert actual["2"] == 1000
    assert actual["12"] == 450


def test_incomes_with_month(data):
    actual = PlanCalculateDaySum(data, 1).get_row("incomes")

    assert actual == 900


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty).get_row("incomes")

    assert actual["1"] == 0
    assert actual["12"] == 0


def test_savings(data):
    actual = PlanCalculateDaySum(data).get_row("savings")

    assert len(actual) == 12
    assert actual["1"] == 190
    assert actual["2"] == 200


def test_savings_with_month(data):
    data.month = 1
    actual = PlanCalculateDaySum(data, 1).get_row("savings")

    assert actual == 190


def test_expenses_free(data):
    actual = PlanCalculateDaySum(data).get_row("expenses_free")

    assert len(actual) == 12
    assert actual["1"] == -40.0
    assert actual["2"] == -170.0


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -40.0),
        (2, -170.0),
        (3, 450.0),
    ],
)
def test_expenses_free_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("expenses_free")

    assert actual == expect


def test_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).get_row("expenses_necessary")

    assert len(actual) == 12
    assert round(actual["1"], 2) == 490
    assert round(actual["2"], 2) == 620


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 490),
        (2, 620),
        (3, 0),
    ],
)
def test_expenses_necessary_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("expenses_necessary")

    assert actual == expect


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 750),
        (2, 900),
        (3, 0),
    ],
)
def test_expenses_full(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("expenses_full")

    assert actual == expect


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -300.0),
        (2, -450.0),
        (3, 450.0),
    ],
)
def test_expenses_remains(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("expenses_remains")

    assert actual == expect


def test_day_input(data):
    actual = PlanCalculateDaySum(data).get_row("day_input")

    assert len(actual) == 12
    assert round(actual["1"], 2) == 25
    assert round(actual["2"], 2) == 26


def test_day_calced(data):
    actual = PlanCalculateDaySum(data).get_row("day_calced")

    assert round(actual["1"], 2) == -1.29
    assert round(actual["2"], 2) == -5.86
    assert round(actual["3"], 2) == 14.52
    assert round(actual["4"], 2) == 15.00


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -1.29),
        (2, -5.86),
        (3, 14.52),
        (4, 15.00),
        (5, 14.52),
        (6, 15.00),
    ],
)
def test_day_calced_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("day_calced")

    assert round(actual, 2) == expect


def test_remains(data):
    actual = PlanCalculateDaySum(data).get_row("remains")

    assert len(actual) == 12
    assert round(actual["1"], 2) == -815.0
    assert round(actual["2"], 2) == -924.0


def test_remains_only_necessary_expenses(data):
    data.necessary = [
        {"month": 5, "amount": 12500},
    ]
    actual = PlanCalculateDaySum(data).get_row("remains")

    assert len(actual) == 12
    assert round(actual["1"], 2) == -815.0
    assert round(actual["2"], 2) == -824.0


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -815.0),
        (2, -924.0),
        (3, 450.0),
    ],
)
def test_remains_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("remains")

    assert round(actual, 2) == expect


def test_additional_necessary(data):
    actual = PlanCalculateDaySum(data).get_row("necessary")

    assert len(actual) == 12
    assert round(actual["1"], 2) == 0
    assert round(actual["2"], 2) == 100


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 0),
        (2, 100),
        (3, 0),
    ],
)
def test_additional_necessary_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month).get_row("necessary")

    assert round(actual, 2) == expect


def test_plans_stats_list(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert len(actual) == 8


def test_plans_stats_incomes_median(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "1. Pajamos (mediana)" == actual[0]["type"]
    assert round(actual[0]["1"], 2) == 450.0
    assert round(actual[0]["2"], 2) == 450.0


def test_plans_stats_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[1]["type"] == "2. Būtinos išlaidos"
    assert round(actual[1]["1"], 2) == 490
    assert round(actual[1]["2"], 2) == 620


def test_plans_stats_expenses_free(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[2]["type"] == "3. Lieka kasdienybei (1 - 2)"
    assert round(actual[2]["1"], 2) == -40.0
    assert round(actual[2]["2"], 2) == -170.0


def test_plans_stats_expenses_free2(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[3]["type"] == "4. Lieka kasdienybei (iš lentelių viršuje)"
    assert round(actual[3]["1"], 2) == 260
    assert round(actual[3]["2"], 2) == 280


def test_plans_stats_expenses_full(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[4]["type"] == "5. Visos išlaidos (1 + 4)"
    assert round(actual[4]["1"], 2) == 750
    assert round(actual[4]["2"], 2) == 900


def test_plans_stats_expenses_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[5]["type"] == "6. Pajamos - Visos išlaidos (1 - 5)"
    assert round(actual[5]["1"], 2) == -300.0
    assert round(actual[5]["2"], 2) == -450.0
    assert round(actual[5]["3"], 2) == 450.0


def test_plans_stats_day_sum(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[6]["type"] == "7. Suma dienai (3 / mėnesio dienų skaičius)"
    assert round(actual[6]["1"], 2) == -1.29
    assert round(actual[6]["2"], 2) == -5.86


def test_plans_stats_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[7]["type"] == "8. Likutis (3 - 7 * mėnesio dienų skaičius)"
    assert round(actual[7]["1"], 2) == -815.0
    assert round(actual[7]["2"], 2) == -924.0


def test_properties_incomes(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.incomes == 900


def test_properties_incomes_avg(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.incomes_avg == 450


def test_properties_savings(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.savings == 190


def test_properties_expenses_necessary(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.expenses_necessary == 490


def test_properties_expenses_free(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.expenses_free == -40


def test_properties_expenses_regular(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.expenses_regular == 260


def test_properties_expenses_remains(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.expenses_remains == -300


def test_properties_day_calced(data):
    obj = PlanCalculateDaySum(data, 1)
    assert round(obj.day_calced, 2) == -1.29


def test_properties_day_input(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.day_input == 25


def test_properties_remains(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.remains == -815


def test_properties_month_len(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.month_len == 31


def test_properties_no_exists(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.X == {}
