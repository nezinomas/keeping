from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ...lib.no_incomes import NoIncomes

XYZ = [
    {"title": "X", "sum": 1},
    {"title": "Y", "sum": 2},
    {"title": "Z", "sum": 4},
]

EXPENSES = st.lists(
    st.fixed_dictionaries(
        {"title": st.sampled_from(["X", "Y", "Z"]), "sum": st.integers(-1000, 1000)}
    ),
    max_size=6,
)
SAVINGS = st.one_of(
    st.just({}), st.fixed_dictionaries({"sum": st.integers(-1000, 1000)})
)
UNNECESSARY = st.lists(st.sampled_from(["X", "Y", "Z", "Taupymas"]), max_size=4)
MONTHS = st.integers(1, 24)


def _data(expenses, savings, unnecessary):
    return SimpleNamespace(
        account_sum=4,
        fund_sum=2,
        pension_sum=1,
        expenses=expenses,
        savings=savings,
        unnecessary=unnecessary,
    )


@pytest.fixture(name="no_incomes_data")
def fixture_data():
    return SimpleNamespace(
        account_sum=4,
        fund_sum=2,
        pension_sum=1,
        expenses=XYZ,
        savings={},
        unnecessary=[],
    )


@pytest.mark.parametrize(
    "savings, unnecessary, months, expect",
    [
        pytest.param({"sum": 2}, ["Z", "Taupymas"], 1, 9, id="cut-one-month"),
        pytest.param({"sum": 2}, ["Z", "Taupymas"], 6, 1.5, id="cut-six-months"),
        pytest.param({"sum": 2}, ["Taupymas"], 1, 9, id="no-expense-cut-one-month"),
        pytest.param({"sum": 2}, ["Taupymas"], 6, 1.5, id="no-expense-cut-six-months"),
        pytest.param({}, [], 1, 7, id="no-savings-one-month"),
        pytest.param({}, [], 6, 1.17, id="no-savings-six-months"),
    ],
)
def test_no_incomes_avg_expenses(savings, unnecessary, months, expect, no_incomes_data):
    no_incomes_data.savings = savings
    no_incomes_data.unnecessary = unnecessary
    obj = NoIncomes(no_incomes_data, months)

    assert round(obj.avg_expenses, 2) == expect


@given(expenses=EXPENSES, savings=SAVINGS, unnecessary=UNNECESSARY, months=MONTHS)
def test_avg_expenses_halves_over_twice_the_months(
    expenses, savings, unnecessary, months
):
    data = _data(expenses, savings, unnecessary)

    actual = NoIncomes(data, 2 * months).avg_expenses

    assert actual == pytest.approx(NoIncomes(data, months).avg_expenses / 2)


@given(expenses=EXPENSES, savings=SAVINGS, unnecessary=UNNECESSARY, months=MONTHS)
def test_avg_expenses_ignores_what_is_unnecessary(
    expenses, savings, unnecessary, months
):
    actual = NoIncomes(_data(expenses, savings, unnecessary), months).avg_expenses

    assert actual == NoIncomes(_data(expenses, savings, []), months).avg_expenses


@pytest.mark.parametrize(
    "savings, unnecessary, months, expect",
    [
        ({"sum": 2}, ["Z", "Taupymas"], 1, 6),
        ({"sum": 2}, ["Z", "Taupymas"], 6, 1),
        ({"sum": 2}, ["Taupymas"], 1, 2),
        ({"sum": 2}, ["Taupymas"], 6, 0.33),
        ({"sum": 0}, [], 1, 0),
    ],
)
def test_no_incomes_cut_sum(savings, unnecessary, months, expect, no_incomes_data):
    no_incomes_data.savings = savings
    no_incomes_data.unnecessary = unnecessary
    obj = NoIncomes(no_incomes_data, months)

    assert round(obj.cut_sum, 2) == expect


def test_no_incomes_summary(no_incomes_data):
    no_incomes_data.savings = {"sum": 2}
    no_incomes_data.unnecessary = ["Z", "Taupymas"]

    actual = NoIncomes(no_incomes_data, 6).summary

    assert len(actual) == 3
    assert actual[0]["title"] == "Pinigai, €"
    assert actual[0]["money_fund"] == 6
    assert actual[0]["money_fund_pension"] == 7
    assert actual[0]["price"] is True

    assert actual[1]["title"] == "Nekeičiant išlaidų, mėn"
    assert round(actual[1]["money_fund"], 2) == 4
    assert round(actual[1]["money_fund_pension"], 2) == 4.67
    assert actual[1]["price"] is False

    assert actual[2]["title"] == "Sumažinus išlaidas, mėn"
    assert round(actual[2]["money_fund"], 2) == 12
    assert round(actual[2]["money_fund_pension"], 2) == 14
    assert actual[2]["price"] is False


@pytest.mark.parametrize(
    "expenses, savings, unnecessary, months, expect_avg, expect_cut",
    [
        pytest.param(
            [
                {"title": "Expense 1", "sum": 100},
                {"title": "Expense 2", "sum": 200},
                {"title": "Expense 3", "sum": 300},
            ],
            {"sum": 500},
            ["Expense 2"],
            12,
            (100 + 200 + 300 + 500) / 12,
            (200 + 500) / 12,
            id="standard-data",
        ),
        pytest.param(
            [{"title": "Expense 1", "sum": 100}],
            {"sum": 0},
            ["Null Expense"],
            1,
            100.0,
            0.0,
            id="unnecessary-title-matches-no-expense",
        ),
        pytest.param(XYZ, {}, ["Z"], 1, 7, 4, id="empty-savings-leave-expenses-alone"),
    ],
)
def test_no_incomes_avg_and_cut_of_other_expenses(
    no_incomes_data, expenses, savings, unnecessary, months, expect_avg, expect_cut
):
    no_incomes_data.expenses = expenses
    no_incomes_data.savings = savings
    no_incomes_data.unnecessary = unnecessary

    obj = NoIncomes(no_incomes_data, months)

    assert obj.avg_expenses == expect_avg
    assert obj.cut_sum == expect_cut


@pytest.mark.parametrize(
    "expenses_sum, expect",
    [
        pytest.param(2, 5, id="normal"),
        pytest.param(0, 0, id="zero_division"),
        pytest.param(-2, -5, id="negative"),
    ],
)
def test_summary_divides_money_by_the_monthly_expenses(
    no_incomes_data, expenses_sum, expect
):
    no_incomes_data.account_sum = 10
    no_incomes_data.fund_sum = 0
    no_incomes_data.pension_sum = 0
    no_incomes_data.expenses = [{"title": "X", "sum": expenses_sum}]

    actual = NoIncomes(no_incomes_data, 1).summary

    assert actual[1]["money_fund"] == expect
    assert actual[2]["money_fund"] == expect
