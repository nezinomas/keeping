import polars as pl
import pytest

from ...lib.calc_day_sum import PlanCalculateDaySum


@pytest.fixture(name="data")
def fixture_data():
    obj = type("PlanCollectData", (object,), {})
    obj.incomes = [
        {
            "january": 400,
            "february": 500,
            "march": 450,
            "april": 450,
            "may": 450,
            "june": 450,
            "july": 450,
            "august": 450,
            "september": 450,
            "october": 450,
            "november": 450,
            "december": 450,
        },
        {
            "january": 500,
            "february": 500,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
        },
    ]
    obj.expenses = [
        {
            "january": 110,
            "february": 120,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
            "necessary": False,
            "title": "T1",
        },
        {
            "january": 130,
            "february": 140,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
            "necessary": True,
            "title": "T2",
        },
        {
            "january": 150,
            "february": 160,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
            "necessary": False,
            "title": "T3",
        },
        {
            "january": 170,
            "february": 180,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
            "necessary": True,
            "title": "T4",
        },
    ]

    obj.savings = [
        {
            "january": 100,
            "february": 110,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
        },
        {
            "january": 90,
            "february": 90,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
        },
    ]

    obj.days = [
        {
            "january": 25,
            "february": 26,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
        },
    ]

    obj.necessary = [
        {
            "january": None,
            "february": 100,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
            "title": "NNN",
        },
    ]

    obj.month_len = {
        "january": 31,
        "february": 29,
        "march": 31,
        "april": 30,
        "may": 31,
        "june": 30,
        "july": 31,
        "august": 31,
        "september": 30,
        "october": 31,
        "november": 30,
        "december": 31,
    }

    return obj


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return type(
        "PlanCollectData",
        (object,),
        {
            "incomes": [],
            "expenses": [],
            "savings": [],
            "days": [],
            "necessary": [],
            "month_len": {
                "january": 31,
                "february": 29,
                "march": 31,
                "april": 30,
                "may": 31,
                "june": 30,
                "july": 31,
                "august": 31,
                "september": 30,
                "october": 31,
                "november": 30,
                "december": 31,
            },
        },
    )


def test_filter_df_wrong_type(data):
    actual = PlanCalculateDaySum(data)._get_row("xxx")

    assert actual == {}


def test_incomes(data):
    actual = PlanCalculateDaySum(data)._get_row("incomes")

    assert len(actual) == 12
    assert actual["january"] == 900
    assert actual["december"] == 450


def test_calc_df_called_once_then_dataframe_not_empty(mocker, data_empty):
    mck = mocker.patch(
        "project.plans.lib.calc_day_sum.PlanCalculateDaySum._calc_df",
        return_value=pl.DataFrame([{"name": "A", "january": 66}]),
    )

    obj = PlanCalculateDaySum(data_empty, 1)

    result1 = obj._get_row("A")
    result2 = obj._get_row("A")

    assert result1 == 66
    assert result2 == 66

    mck.assert_called_once()


def test_calc_df_called_once_then_dataframe_is_empty(mocker, data_empty):
    mck = mocker.patch(
        "project.plans.lib.calc_day_sum.PlanCalculateDaySum._calc_df",
        return_value=pl.DataFrame(),
    )

    obj = PlanCalculateDaySum(data_empty, 1)

    result1 = obj._get_row("A")
    result2 = obj._get_row("B")

    assert result1 == {}
    assert result2 == {}

    mck.assert_called_once()


def test_incomes_with_month(data):
    actual = PlanCalculateDaySum(data, 1)._get_row("incomes")

    assert actual == 900


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty)._get_row("incomes")

    assert actual["january"] == 0
    assert actual["december"] == 0


def test_savings(data):
    actual = PlanCalculateDaySum(data)._get_row("savings")

    assert len(actual) == 12
    assert round(actual["january"], 2) == 190
    assert round(actual["february"], 2) == 200


def test_savings_with_month(data):
    data.month = 1
    actual = PlanCalculateDaySum(data, 1)._get_row("savings")

    assert actual == 190


def test_expenses_free(data):
    actual = PlanCalculateDaySum(data)._get_row("expenses_free")

    assert len(actual) == 12
    assert round(actual["january"], 2) == -40.0
    assert round(actual["february"], 2) == -170.0


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -40.0),
        (2, -170.0),
        (3, 450.0),
    ],
)
def test_expenses_free_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("expenses_free")

    assert actual == expect


def test_expenses_necessary(data):
    actual = PlanCalculateDaySum(data)._get_row("expenses_necessary")

    assert len(actual) == 12
    assert round(actual["january"], 2) == 490
    assert round(actual["february"], 2) == 620


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 490),
        (2, 620),
        (3, 0),
    ],
)
def test_expenses_necessary_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("expenses_necessary")

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
    actual = PlanCalculateDaySum(data, month)._get_row("expenses_full")

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
    actual = PlanCalculateDaySum(data, month)._get_row("expenses_remains")

    assert actual == expect


def test_day_calced(data):
    actual = PlanCalculateDaySum(data)._get_row("day_calced")

    assert len(actual) == 12
    assert round(actual["january"], 2) == -1.29
    assert round(actual["february"], 2) == -5.86


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -1.29),
        (2, -5.86),
        (3, 14.52),
    ],
)
def test_day_calced_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("day_calced")

    assert round(actual, 2) == expect


def test_day_input(data):
    actual = PlanCalculateDaySum(data)._get_row("day_input")

    assert len(actual) == 12
    assert round(actual["january"], 2) == 25
    assert round(actual["february"], 2) == 26


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 25),
        (2, 26),
        (3, 0),
    ],
)
def test_day_input_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("day_input")

    assert round(actual, 2) == expect


def test_remains(data):
    actual = PlanCalculateDaySum(data)._get_row("remains")

    assert len(actual) == 12
    assert round(actual["january"], 2) == -815.0
    assert round(actual["february"], 2) == -924.0


def test_remains_only_necessary_expenses(data):
    data.necessary = [
        {
            "january": None,
            "february": None,
            "march": None,
            "april": None,
            "may": 12500,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": None,
        }
    ]
    actual = PlanCalculateDaySum(data)._get_row("remains")

    assert len(actual) == 12
    assert round(actual["january"], 2) == -815.0
    assert round(actual["february"], 2) == -824.0


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -815.0),
        (2, -924.0),
        (3, 450.0),
    ],
)
def test_remains_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("remains")

    assert round(actual, 2) == expect


def test_additional_necessary(data):
    actual = PlanCalculateDaySum(data)._get_row("necessary")

    assert len(actual) == 12
    assert round(actual["january"], 2) == 0
    assert round(actual["february"], 2) == 100


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 0),
        (2, 100),
        (3, 0),
    ],
)
def test_additional_necessary_with_month(month, expect, data):
    actual = PlanCalculateDaySum(data, month)._get_row("necessary")

    assert round(actual, 2) == expect


def test_plans_stats_list(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert len(actual) == 8


def test_plans_stats_incomes_median(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "1. Pajamos (mediana)" == actual[0].type
    assert round(actual[0].january, 2) == 450.0
    assert round(actual[0].february, 2) == 450.0


def test_plans_stats_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[1].type == "2. Būtinos išlaidos"
    assert round(actual[1].january, 2) == 490
    assert round(actual[1].february, 2) == 620


def test_plans_stats_expenses_free(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[2].type == "3. Lieka kasdienybei (1 - 2)"
    assert round(actual[2].january, 2) == -40.0
    assert round(actual[2].february, 2) == -170.0


def test_plans_stats_expenses_free2(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[3].type == "4. Lieka kasdienybei (iš lentelių viršuje)"
    assert round(actual[3].january, 2) == 260
    assert round(actual[3].february, 2) == 280


def test_plans_stats_expenses_full(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[4].type == "5. Visos išlaidos (1 + 4)"
    assert round(actual[4].january, 2) == 750
    assert round(actual[4].february, 2) == 900


def test_plans_stats_expenses_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[5].type == "6. Pajamos - Visos išlaidos (1 - 5)"
    assert round(actual[5].january, 2) == -300.0
    assert round(actual[5].february, 2) == -450.0
    assert round(actual[5].march, 2) == 450.0


def test_plans_stats_day_sum(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[6].type == "7. Suma dienai (3 / mėnesio dienų skaičius)"
    assert round(actual[6].january, 2) == -1.29
    assert round(actual[6].february, 2) == -5.86


def test_plans_stats_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[7].type == "8. Likutis (3 - 7 * mėnesio dienų skaičius)"
    assert round(actual[7].january, 2) == -815.0
    assert round(actual[7].february, 2) == -924.0


def test_targets(data):
    obj = PlanCalculateDaySum(data, 2)

    actual = obj.monthly_plan_by_category

    expect = {"T1": 120, "T2": 140, "T3": 160, "T4": 180, "NNN": 100, "Taupymas": 200}

    assert actual == expect


def test_targets_with_same_title_for_expense_and_necessary(data):
    data.necessary[0]["title"] = "T1"

    obj = PlanCalculateDaySum(data, 2)

    actual = obj.monthly_plan_by_category

    expect = {"T1": 220, "T2": 140, "T3": 160, "T4": 180, "Taupymas": 200}

    assert actual == expect


def test_targets_no_month(data):
    obj = PlanCalculateDaySum(data)

    actual = obj.monthly_plan_by_category

    assert not actual


def test_target_with_nones(data_empty):
    data_empty.expenses = [
        {"january": 0, "february": 0, "necessary": False, "title": "T1"}
    ]

    obj = PlanCalculateDaySum(data_empty, 2)

    actual = obj.monthly_plan_by_category

    expect = {"T1": 0}

    assert actual == expect


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


def test_properties_expenses_free2(data):
    obj = PlanCalculateDaySum(data, 1)
    assert obj.expenses_free2 == 260


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


@pytest.mark.xfail
def test_properties_no_exists(data):
    obj = PlanCalculateDaySum(data, 1)
    obj.X
