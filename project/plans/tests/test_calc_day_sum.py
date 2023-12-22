import pytest

from ..lib.calc_day_sum import PlanCalculateDaySum


@pytest.fixture(name="data")
def fixture_data():
    obj = type("PlanCollectData", (object,), {})

    obj.year = 2020
    obj.month = 0


    obj.incomes = [
        {
            "january": 400,
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

    return obj


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return type(
        "PlanCollectData",
        (object,),
        {
            "year": 2020,
            "month": 0,
            "incomes": [],
            "expenses": [],
            "savings": [],
            "days": [],
            "necessary": [],
        },
    )


def test_incomes(data):
    actual = PlanCalculateDaySum(data).incomes

    assert len(actual) == 12
    assert round(actual["january"], 2) == 900
    assert actual["december"] == 0


def test_incomes_with_month(data):
    data.month = 1
    actual = PlanCalculateDaySum(data).incomes

    assert round(actual, 2) == 900


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty).incomes

    assert actual["january"] == 0
    assert actual["december"] == 0


def test_savings(data):
    actual = PlanCalculateDaySum(data).savings

    assert len(actual) == 12
    assert round(actual["january"], 2) == 190
    assert round(actual["february"], 2) == 200


def test_savings_with_month(data):
    data.month = 1
    actual = PlanCalculateDaySum(data).savings

    assert round(actual, 2) == 190


def test_expenses_free(data):
    actual = PlanCalculateDaySum(data).expenses_free

    assert len(actual) == 12
    assert round(actual["january"], 2) == 260
    assert round(actual["february"], 2) == 280


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 260),
        (2, 280),
        (3, 0),
    ],
)
def test_expenses_free_with_month(month, expect, data):
    data.month = month
    actual = PlanCalculateDaySum(data).expenses_free

    assert round(actual, 2) == expect


def test_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).expenses_necessary

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
    data.month = month
    actual = PlanCalculateDaySum(data).expenses_necessary

    assert round(actual, 2) == expect


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 750),
        (2, 900),
        (3, 0),
    ],
)
def test_expenses_full(month, expect, data):
    data.month = month
    actual = PlanCalculateDaySum(data).expenses_full

    assert round(actual, 2) == expect


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -591.67),
        (2, -741.67),
        (3, 158.33),
    ],
)
def test_expenses_remains(month, expect, data):
    data.month = month
    actual = PlanCalculateDaySum(data).expenses_remains

    assert round(actual, 2) == expect


def test_day_calced(data):
    actual = PlanCalculateDaySum(data).day_calced

    assert len(actual) == 12
    assert round(actual["january"], 2) == 8.39
    assert round(actual["february"], 2) == 9.66


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 8.39),
        (2, 9.66),
        (3, 0),
    ],
)
def test_day_calced_with_month(month, expect, data):
    data.month = month
    actual = PlanCalculateDaySum(data).day_calced

    assert round(actual, 2) == expect


def test_day_input(data):
    actual = PlanCalculateDaySum(data).day_input

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
    data.month = month
    actual = PlanCalculateDaySum(data).day_input

    assert round(actual, 2) == expect


def test_remains(data):
    actual = PlanCalculateDaySum(data).remains

    assert len(actual) == 12
    assert round(actual["january"], 2) == -515
    assert round(actual["february"], 2) == -474


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
    actual = PlanCalculateDaySum(data).remains

    assert len(actual) == 12
    assert round(actual["january"], 2) == -515
    assert round(actual["february"], 2) == -474


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -515),
        (2, -474),
        (3, 0),
    ],
)
def test_remains_with_month(month, expect, data):
    data.month = month
    actual = PlanCalculateDaySum(data).remains

    assert round(actual, 2) == expect


def test_additional_necessary(data):
    actual = PlanCalculateDaySum(data).necessary

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
    data.month = month
    actual = PlanCalculateDaySum(data).necessary

    assert round(actual, 2) == expect


def test_plans_stats_list(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert len(actual) == 5


def test_plans_stats_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "Būtinos išlaidos (1)" == actual[0].type
    assert round(actual[0].january, 2) == 490
    assert round(actual[0].february, 2) == 620


def test_plans_stats_expenses_free(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[1].type == "Lieka kasdienybei (2)"
    assert round(actual[1].january, 2) == 260
    assert round(actual[1].february, 2) == 280


def test_plans_stats_expenses_full(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[2].type == "(1) + (2)"
    assert round(actual[2].january, 2) == 750
    assert round(actual[2].february, 2) == 900


def test_plans_stats_day_sum(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "Suma dienai" in actual[3].type
    assert round(actual[3].january, 2) == 8.39
    assert round(actual[3].february, 2) == 9.66


def test_plans_stats_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[4].type == "Likutis"
    assert round(actual[4].january, 2) == -515
    assert round(actual[4].february, 2) == -474


def test_targets(data):
    data.month = 2
    obj = PlanCalculateDaySum(data)

    actual = obj.targets

    expect = {"T1": 120, "T2": 140, "T3": 160, "T4": 180, "NNN": 100}

    assert actual == expect


def test_targets_with_same_title_for_expense_and_necessary(data):
    data.necessary[0]["title"] = "T1"

    data.month = 2
    obj = PlanCalculateDaySum(data)

    actual = obj.targets

    expect = {"T1": 220, "T2": 140, "T3": 160, "T4": 180}

    assert actual == expect


def test_targets_no_month(data):
    obj = PlanCalculateDaySum(data)

    actual = obj.targets

    assert not actual


def test_target_with_nones(data_empty):
    data_empty.month = 2
    data_empty.expenses = [{"january": 0, "february": 0, "necessary": False, "title": "T1"}]

    obj = PlanCalculateDaySum(data_empty)

    actual = obj.targets

    expect = {"T1": 0}

    assert actual == expect
