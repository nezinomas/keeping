import pytest

from ...lib.calc_day_sum import OVER, WITHIN, DataDto, PlanCalculateDaySum

MONTH_LEN = [{"month": m, "amount": 100} for m in range(1, 13)]
INCOMES = [{"month": m, "amount": 2500} for m in range(1, 13)]


@pytest.fixture(name="data")
def fixture_data():
    return DataDto(
        incomes=INCOMES,
        expenses_regular=[],
        expenses_necessary=[],
        savings=[],
        per_day=[
            {"month": 1, "amount": 30},
            {"month": 2, "amount": 25},
        ],
        necessary=[],
        month_len=MONTH_LEN,
    )


def test_day_plan_states_over_when_day_plan_is_above_sum_per_day(data):
    actual = PlanCalculateDaySum(data).day_plan_states()

    assert actual["1"] == OVER


def test_day_plan_states_within_when_day_plan_equals_sum_per_day(data):
    actual = PlanCalculateDaySum(data).day_plan_states()

    assert actual["2"] == WITHIN


def test_day_plan_states_only_over_months_are_over(data):
    actual = PlanCalculateDaySum(data).day_plan_states()

    over_months = [month for month, state in actual.items() if state == OVER]

    assert over_months == ["1"]
    assert all(actual[m] == WITHIN for m in actual if m != "1")


def test_day_plan_states_has_all_twelve_months(data):
    actual = PlanCalculateDaySum(data).day_plan_states()

    assert list(actual.keys()) == [str(i) for i in range(1, 13)]


def test_day_plan_states_within_without_a_day_plan_when_sum_per_day_is_negative():
    data = DataDto(
        incomes=INCOMES,
        expenses_regular=[],
        expenses_necessary=[],
        savings=[{"month": m, "amount": 5000} for m in range(1, 13)],
        per_day=[],
        necessary=[],
        month_len=MONTH_LEN,
    )

    actual = PlanCalculateDaySum(data).day_plan_states()

    assert actual["1"] == WITHIN
