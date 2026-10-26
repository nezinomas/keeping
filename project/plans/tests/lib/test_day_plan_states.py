import pytest

from ...lib.calc_day_sum import DataDto, PlanCalculateDaySum
from ...lib.month_states import MONTH_NUMS, OVER, WITHIN

MONTH_LEN = [{"month": m, "amount": 100} for m in range(1, 13)]
INCOMES = [{"month": m, "amount": 2500} for m in range(1, 13)]


@pytest.mark.parametrize(
    "savings, per_day, over",
    [
        pytest.param(
            [],
            [{"month": 1, "amount": 30}, {"month": 2, "amount": 25}],
            ["1"],
            id="above_is_over_equal_is_within",
        ),
        pytest.param(
            [{"month": m, "amount": 5000} for m in range(1, 13)],
            [],
            [],
            id="no_day_plan_is_within_a_negative_sum_per_day",
        ),
    ],
)
def test_day_plan_states(savings, per_day, over):
    data = DataDto(
        incomes=INCOMES,
        expenses_regular=[],
        expenses_necessary=[],
        savings=savings,
        per_day=per_day,
        necessary=[],
        month_len=MONTH_LEN,
    )

    actual = PlanCalculateDaySum(data).day_plan_states()

    assert list(actual.items()) == [
        (month, OVER if month in over else WITHIN) for month in MONTH_NUMS
    ]
