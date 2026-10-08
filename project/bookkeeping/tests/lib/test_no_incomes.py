from types import SimpleNamespace

import pytest
from hypothesis import example, given
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


def test_no_incomes_empty_savings_leave_expenses_alone(no_incomes_data):
    no_incomes_data.unnecessary = ["Z"]
    obj = NoIncomes(no_incomes_data, 1)

    assert obj.avg_expenses == 7
    assert obj.cut_sum == 4


@given(expenses=EXPENSES, savings=SAVINGS, unnecessary=UNNECESSARY, months=MONTHS)
@example(XYZ, {"sum": 2}, ["Z", "Taupymas"], 1)
@example(XYZ, {"sum": 2}, ["Z", "Taupymas"], 6)
@example(XYZ, {"sum": 2}, ["Taupymas"], 1)
@example(XYZ, {"sum": 2}, ["Taupymas"], 6)
@example(XYZ, {}, [], 1)
@example(XYZ, {}, [], 6)
def test_no_incomes_avg_expenses(expenses, savings, unnecessary, months):
    data = SimpleNamespace(
        account_sum=4,
        fund_sum=2,
        pension_sum=1,
        expenses=expenses,
        savings=savings,
        unnecessary=unnecessary,
    )
    spent = sum(x["sum"] for x in expenses) + savings.get("sum", 0)

    assert NoIncomes(data, months).avg_expenses == spent / months


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


@pytest.fixture
def no_incomes_data_class():
    return SimpleNamespace(
        account_sum=1000,
        fund_sum=500,
        pension_sum=200,
        expenses=[
            {"title": "Expense 1", "sum": 100},
            {"title": "Expense 2", "sum": 200},
            {"title": "Expense 3", "sum": 300},
        ],
        savings={"sum": 500},
        unnecessary=["Expense 2"],
    )


def test_summary_property(no_incomes_data_class):
    no_incomes = NoIncomes(no_incomes_data_class, months=12)
    summary = no_incomes.summary

    assert len(summary) == 3
    assert summary[0]["title"] == "Pinigai, €"
    assert summary[0]["money_fund"] == 1500
    assert summary[0]["money_fund_pension"] == 1700

    assert summary[1]["title"] == "Nekeičiant išlaidų, mėn"
    assert summary[1]["money_fund"] == 1500 / no_incomes.avg_expenses
    assert summary[1]["money_fund_pension"] == 1700 / no_incomes.avg_expenses

    assert summary[2]["title"] == "Sumažinus išlaidas, mėn"
    assert summary[2]["money_fund"] == 1500 / (
        no_incomes.avg_expenses - no_incomes.cut_sum
    )
    assert summary[2]["money_fund_pension"] == 1700 / (
        no_incomes.avg_expenses - no_incomes.cut_sum
    )


def test_calc_method_handles_standard_data(no_incomes_data_class):
    no_incomes = NoIncomes(no_incomes_data_class, months=12)

    assert no_incomes.avg_expenses == (100 + 200 + 300 + 500) / 12
    assert no_incomes.cut_sum == (200 + 500) / 12


def test_unnecessary_title_matching_no_expense_cuts_nothing(no_incomes_data_class):
    no_incomes_data_class.expenses = [
        {"title": "Expense 1", "sum": 100},
    ]
    no_incomes_data_class.savings = {"sum": 0}
    no_incomes_data_class.unnecessary = ["Null Expense"]

    no_incomes = NoIncomes(no_incomes_data_class, months=1)

    assert no_incomes.avg_expenses == 100.0
    assert no_incomes.cut_sum == 0.0


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
