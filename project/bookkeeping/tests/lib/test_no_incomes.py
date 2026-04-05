from types import SimpleNamespace

import pytest

from ...lib.no_incomes import NoIncomes


@pytest.fixture(name="no_incomes_data")
def fixture_data():
    return SimpleNamespace(
        year=1999,
        months=6,
        account_sum=4,
        fund_sum=2,
        pension_sum=1,
        expenses=[
            {"title": "X", "sum": 1},
            {"title": "Y", "sum": 2},
            {"title": "Z", "sum": 4},
        ],
        savings={},
        unnecessary=[],
    )


@pytest.mark.parametrize(
    "savings, unnecessary, months, expect",
    [
        # Standard Data
        ({"sum": 2}, ["Z", "Taupymas"], 1, 9),
        ({"sum": 2}, ["Z", "Taupymas"], 6, 1.5),
        ({"sum": 2}, ["Taupymas"], 1, 9),
        ({"sum": 2}, ["Taupymas"], 6, 1.5),
        ({}, [], 1, 7),
        ({}, [], 6, 1.17),
        # EDGE CASES: Database returning None
        ({"sum": None}, [], 1, 7),  # Empty savings aggregate
        (None, [], 1, 7),  # Complete absence of savings data
        # EDGE CASES: Direct value inputs (checking fallback type support)
        (5.5, [], 1, 12.5),  # Float provided instead of dict
        (10, [], 1, 17),  # Int provided instead of dict
    ],
)
def test_no_incomes_avg_expenses(savings, unnecessary, months, expect, no_incomes_data):
    no_incomes_data.savings = savings
    no_incomes_data.unnecessary = unnecessary
    no_incomes_data.months = months
    obj = NoIncomes(no_incomes_data)

    assert round(obj.avg_expenses, 2) == expect


@pytest.mark.parametrize(
    "savings, unnecessary, months, expect",
    [
        # Standard Data
        ({"sum": 2}, ["Z", "Taupymas"], 1, 6),
        ({"sum": 2}, ["Z", "Taupymas"], 6, 1),
        ({"sum": 2}, ["Taupymas"], 1, 2),
        ({"sum": 2}, ["Taupymas"], 6, 0.33),
        ({}, [], 1, 0),
        ({}, [], 6, 0),
        # EDGE CASES: Database returning None & Mixed types
        ({"sum": None}, ["Z"], 1, 4),  # Empty savings aggregate
        (None, ["Z"], 1, 4),  # Complete absence of savings data
        (5.5, ["Z"], 1, 9.5),  # Float provided instead of dict
    ],
)
def test_no_incomes_cut_sum(savings, unnecessary, months, expect, no_incomes_data):
    no_incomes_data.savings = savings
    no_incomes_data.unnecessary = unnecessary
    no_incomes_data.months = months
    obj = NoIncomes(no_incomes_data)

    assert round(obj.cut_sum, 2) == expect


def test_no_incomes_summary(no_incomes_data):
    no_incomes_data.savings = {"sum": 2}
    no_incomes_data.unnecessary = ["Z", "Taupymas"]

    actual = NoIncomes(no_incomes_data).summary

    assert actual[0]["title"] == "Pinigai, €"
    assert actual[0]["money_fund"] == 6
    assert actual[0]["money_fund_pension"] == 7
    assert actual[0]["price"] is True  # Verifying the currency flag

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
        year=1999,
        months=12,
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
    no_incomes = NoIncomes(no_incomes_data_class)
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
    no_incomes = NoIncomes(no_incomes_data_class)

    assert no_incomes.avg_expenses == (100 + 200 + 300 + 500) / 12
    assert no_incomes.cut_sum == (200 + 500) / 12


def test_calc_method_handles_none_values_from_database(no_incomes_data_class):
    # Simulate Django returning None for empty/null database aggregations
    no_incomes_data_class.expenses = [
        {"title": "Expense 1", "sum": 100},
        {"title": "Null Expense", "sum": None},  # DB returned None
        {"sum": 50},  # Missing title key entirely
    ]
    no_incomes_data_class.savings = {"sum": None}
    no_incomes_data_class.unnecessary = ["Null Expense"]
    no_incomes_data_class.months = 1

    no_incomes = NoIncomes(no_incomes_data_class)

    # Expected: (100 + 0 + 50 + 0) / 1 = 150
    assert no_incomes.avg_expenses == 150.0
    # Expected: (0 + 0) / 1 = 0
    assert no_incomes.cut_sum == 0.0


def test_div_method(no_incomes_data_class):
    no_incomes = NoIncomes(no_incomes_data_class)

    result_normal = no_incomes._div(10, 2)
    result_zero_division = no_incomes._div(10, 0)
    result_negative = no_incomes._div(10, -2)

    assert result_normal == 5
    assert result_zero_division == 0
    assert result_negative == -5
