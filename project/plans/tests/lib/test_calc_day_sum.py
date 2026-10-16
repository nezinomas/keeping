from dataclasses import replace

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.calc_day_sum import (
    CalcRow,
    DataDto,
    InputRow,
    PlanCalculateDaySum,
    PlanCollectData,
)

MONTH_LEN = [
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


def make_data(**changes):
    data = DataDto(
        incomes=[
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
        ],
        expenses_regular=[
            {"month": 1, "amount": 260},
            {"month": 2, "amount": 280},
        ],
        expenses_necessary=[
            {"month": 1, "amount": 300},
            {"month": 2, "amount": 320},
        ],
        savings=[
            {"month": 1, "amount": 190},
            {"month": 2, "amount": 200},
        ],
        per_day=[
            {"month": 1, "amount": 25},
            {"month": 2, "amount": 26},
        ],
        necessary=[
            {"month": 2, "amount": 100},
        ],
        month_len=MONTH_LEN,
    )

    return replace(data, **changes)


@pytest.fixture(name="data")
def fixture_data():
    return make_data()


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return DataDto(
        incomes=[],
        expenses_regular=[],
        expenses_necessary=[],
        savings=[],
        per_day=[],
        necessary=[],
        month_len=MONTH_LEN,
    )


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty).row(InputRow.INCOMES)

    assert actual["1"] == 0
    assert actual["12"] == 0


# Pinned values of the one fixture dataset; day_calced is held to the cent.
CENT = 0.005
TWELVE_MONTHS = [
    pytest.param(InputRow.INCOMES, {1: 900, 2: 1000, 12: 450}, id="incomes"),
    pytest.param(CalcRow.INCOMES_AVG, {1: 450, 2: 450}, id="incomes_avg"),
    pytest.param(InputRow.SAVINGS, {1: 190, 2: 200}, id="savings"),
    pytest.param(InputRow.EXPENSES_REGULAR, {1: 260, 2: 280}, id="expenses_regular"),
    pytest.param(
        CalcRow.EXPENSES_NECESSARY, {1: 490, 2: 620, 3: 0}, id="expenses_necessary"
    ),
    pytest.param(CalcRow.EXPENSES_FREE, {1: -40, 2: -170, 3: 450}, id="expenses_free"),
    pytest.param(CalcRow.EXPENSES_FULL, {1: 750, 2: 900, 3: 0}, id="expenses_full_row"),
    pytest.param(
        CalcRow.EXPENSES_REMAINS, {1: -300, 2: -450, 3: 450}, id="expenses_remains_row"
    ),
    pytest.param(InputRow.DAY_PLAN, {1: 25, 2: 26}, id="day_input"),
    pytest.param(
        CalcRow.SUM_PER_DAY,
        {
            1: pytest.approx(-1.29, abs=CENT),
            2: pytest.approx(-5.86, abs=CENT),
            3: pytest.approx(14.52, abs=CENT),
            4: pytest.approx(15.00, abs=CENT),
            5: pytest.approx(14.52, abs=CENT),
            6: pytest.approx(15.00, abs=CENT),
        },
        id="day_calced",
    ),
    pytest.param(CalcRow.REMAINS, {1: -815, 2: -924, 3: 450}, id="remains"),
    pytest.param(InputRow.NECESSARY, {1: 0, 2: 100, 3: 0}, id="additional_necessary"),
    pytest.param(InputRow.MONTH_LEN, {1: 31}, id="properties_month_len"),
]


@pytest.mark.parametrize("row, cells", TWELVE_MONTHS)
def test_row_of_twelve_months(row, cells, data):
    actual = PlanCalculateDaySum(data).row(row)

    assert len(actual) == 12
    for month, expect in cells.items():
        assert actual[str(month)] == expect


@example(row="incomes", month=1)
@example(row="savings", month=1)
@example(row="expenses_free", month=1)
@example(row="expenses_free", month=2)
@example(row="expenses_free", month=3)
@example(row="expenses_remains", month=1)
@example(row="expenses_remains", month=2)
@example(row="expenses_remains", month=3)
@example(row="expenses_necessary", month=1)
@example(row="expenses_necessary", month=2)
@example(row="expenses_necessary", month=3)
@example(row="expenses_full", month=1)
@example(row="expenses_full", month=2)
@example(row="expenses_full", month=3)
@example(row="day_calced", month=1)
@example(row="day_calced", month=2)
@example(row="day_calced", month=3)
@example(row="day_calced", month=4)
@example(row="day_calced", month=5)
@example(row="day_calced", month=6)
@example(row="remains", month=1)
@example(row="remains", month=2)
@example(row="remains", month=3)
@example(row="necessary", month=1)
@example(row="necessary", month=2)
@example(row="necessary", month=3)
@example(row="incomes_avg", month=1)
@example(row="expenses_regular", month=1)
@example(row="day_input", month=1)
@example(row="month_len", month=1)
@given(row=st.sampled_from([*InputRow, *CalcRow]), month=st.integers(1, 12))
def test_row_of_one_month_is_its_cell_of_twelve(row, month):
    data = make_data()

    actual = PlanCalculateDaySum(data, month).row(row)

    assert actual == PlanCalculateDaySum(data).row(row)[str(month)]


def test_remains_only_necessary_expenses():
    data = make_data(necessary=[{"month": 5, "amount": 12500}])

    actual = PlanCalculateDaySum(data).row(CalcRow.REMAINS)

    assert len(actual) == 12
    assert round(actual["1"], 2) == -815.0
    assert round(actual["2"], 2) == -824.0


def test_rows_are_calculated_once(data):
    obj = PlanCalculateDaySum(data)
    _ = obj.row(InputRow.MONTH_LEN)

    data.incomes.clear()

    assert obj.row(CalcRow.INCOMES_AVG)["1"] == 450


@pytest.mark.django_db
def test_plan_collect_data_formats_month_len_as_tall_list(main_user):
    obj = PlanCollectData(user=main_user, year=2024).get_data()

    assert obj.month_len == MONTH_LEN
