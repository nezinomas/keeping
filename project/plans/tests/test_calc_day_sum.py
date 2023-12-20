import pytest

from ..lib.calc_day_sum import PlanCalculateDaySum


@pytest.fixture(name="data")
def fixture_data():
    obj = type("PlanCollectData", (object,), {})

    obj.year = 2020
    obj.month = 0

    obj.incomes = [
        {"january": 400, "february": 500},
        {"january": 500, "february": 500},
    ]
    obj.expenses = [
        {"january": 110, "february": 120, "necessary": False, "title": "T1"},
        {"january": 130, "february": 140, "necessary": True, "title": "T2"},
        {"january": 150, "february": 160, "necessary": False, "title": "T3"},
        {"january": 170, "february": 180, "necessary": True, "title": "T4"},
    ]

    obj.savings = [
        {"january": 100, "february": 110},
        {"january": 90, "february": 90},
    ]

    obj.days = [
        {"january": 25, "february": 26},
    ]

    obj.necessary = [
        {"february": 100},
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
    assert round(actual["january"], 2) == 410
    assert round(actual["february"], 2) == 380


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 410),
        (2, 380),
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


def test_day_calced(data):
    actual = PlanCalculateDaySum(data).day_calced

    assert len(actual) == 12
    assert round(actual["january"], 2) == 13.23
    assert round(actual["february"], 2) == 13.10


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 13.23),
        (2, 13.10),
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
    assert round(actual["january"], 2) == -365
    assert round(actual["february"], 2) == -374


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
    assert round(actual["january"], 2) == -365
    assert round(actual["february"], 2) == -274


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, -365),
        (2, -374),
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

    assert len(actual) == 4


def test_plans_stats_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "Būtinos išlaidos" == actual[0].type
    assert round(actual[0].january, 2) == 490
    assert round(actual[0].february, 2) == 620


def test_plans_stats_expenses_free(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[1].type == "Lieka kasdienybei"
    assert round(actual[1].january, 2) == 410
    assert round(actual[1].february, 2) == 380


def test_plans_stats_day_sum(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert "Suma dienai" in actual[2].type
    assert round(actual[2].january, 2) == 13.23
    assert round(actual[2].february, 2) == 13.10


def test_plans_stats_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[3].type == "Likutis"
    assert round(actual[3].january, 2) == -365
    assert round(actual[3].february, 2) == -374


def test_targets(data):
    data.month = 1
    obj = PlanCalculateDaySum(data)

    actual = obj.targets

    expect = {"T1": 110, "T2": 130, "T3": 150, "T4": 170}

    assert actual == expect


def test_targets_no_month(data):
    obj = PlanCalculateDaySum(data)

    actual = obj.targets

    assert not actual


def test_target_with_nones(data_empty):
    data_empty.month = 1
    data_empty.expenses = [{"january": 0, "necessary": False, "title": "T1"}]

    obj = PlanCalculateDaySum(data_empty)

    actual = obj.targets

    expect = {"T1": 0}

    assert actual == expect
