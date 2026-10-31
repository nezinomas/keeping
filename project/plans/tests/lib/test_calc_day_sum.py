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
from ..day_sum_data import MONTH_LEN, make_data


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
@example(row="day_calced", month=2)
@example(row="remains", month=12)
@given(row=st.sampled_from([*InputRow, *CalcRow]), month=st.integers(1, 12))
def test_cell_is_its_month_of_the_row(row, month):
    obj = PlanCalculateDaySum(make_data())

    actual = obj.cell(row, month)

    assert actual == obj.row(row)[str(month)]


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
