import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseTypeFactory
from ...journals.factories import JournalFactory
from ...savings.factories import SavingTypeFactory
from .. import views
from ..lib.no_incomes import NoIncomes

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                          NoIncomes View
# ---------------------------------------------------------------------------------------
def test_view_func():
    view = resolve("/bookkeeping/no_incomes/")

    assert views.NoIncomes == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:no_incomes")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_not_necessary(client_logged):
    j = JournalFactory()
    e1 = ExpenseTypeFactory(title="XXX")
    e2 = ExpenseTypeFactory(title="YYY")
    SavingTypeFactory()

    j.unnecessary_savings = True
    j.unnecessary_expenses = json.dumps([e1.pk, e2.pk])
    j.save()

    url = reverse("bookkeeping:no_incomes")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert (
        "Nebūtinos išlaidos, kurių galima atsisakyti:\n- XXX\n- YYY\n- Taupymas"
        in actual
    )


def test_template_month_value():
    with open(Path(__file__).cwd() / 'project/bookkeeping/templates/bookkeeping/includes/no_incomes.html') as f:
        template = Template(f.read())

    ctx = Context({
        "no_incomes": [
            {"title": "x", "money_fund": 11, "money_fund_pension": 22, "price": True},
            {"title": "y", "money_fund": 33, "money_fund_pension": 44, "price": False}
        ],
    })
    actual = template.render(ctx)

    # price
    assert "0,11" in actual
    assert "0,22" in actual

    # month
    assert "33,0" in actual
    assert "44,0" in actual


# ---------------------------------------------------------------------------------------
#                                                                        NoIncomes Helper
# ---------------------------------------------------------------------------------------
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
        ({"sum": 2}, ["Z", "Taupymas"], 1, 9),
        ({"sum": 2}, ["Z", "Taupymas"], 6, 1.5),
        ({"sum": 2}, ["Taupymas"], 1, 9),
        ({"sum": 2}, ["Taupymas"], 6, 1.5),
        ({}, [], 1, 7),
        ({}, [], 6, 1.17),
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
        ({"sum": 2}, ["Z", "Taupymas"], 1, 6),
        ({"sum": 2}, ["Z", "Taupymas"], 6, 1),
        ({"sum": 2}, ["Taupymas"], 1, 2),
        ({"sum": 2}, ["Taupymas"], 6, 0.33),
        ({}, [], 1, 0),
        ({}, [], 6, 0),
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

    assert actual[1]["title"] == "Nekeičiant išlaidų, mėn"
    assert round(actual[1]["money_fund"], 2) == 4
    assert round(actual[1]["money_fund_pension"], 2) == 4.67

    assert actual[2]["title"] == "Sumažinus išlaidas, mėn"
    assert round(actual[2]["money_fund"], 2) == 12
    assert round(actual[2]["money_fund_pension"], 2) == 14


@pytest.fixture
def no_incomes_data_class():
    # Create a sample NoIncomesData object for testing
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
        unnecessary=["Expense 2"]
    )


def test_summary_property(no_incomes_data_class):
    # Arrange
    no_incomes = NoIncomes(no_incomes_data_class)

    # Act
    summary = no_incomes.summary

    # Assert
    assert len(summary) == 3
    assert summary[0]["title"] == "Pinigai, €"
    assert summary[0]["money_fund"] == 1500
    assert summary[0]["money_fund_pension"] == 1700

    assert summary[1]["title"] == "Nekeičiant išlaidų, mėn"
    assert summary[1]["money_fund"] == 1500 / no_incomes.avg_expenses
    assert summary[1]["money_fund_pension"] == 1700 / no_incomes.avg_expenses

    assert summary[2]["title"] == "Sumažinus išlaidas, mėn"
    assert summary[2]["money_fund"] == 1500 / (no_incomes.avg_expenses - no_incomes.cut_sum)
    assert summary[2]["money_fund_pension"] == 1700 / (no_incomes.avg_expenses - no_incomes.cut_sum)


def test_calc_method(no_incomes_data_class):
    # Arrange
    no_incomes = NoIncomes(no_incomes_data_class)

    # Act
    no_incomes._calc()

    # Assert
    assert no_incomes.avg_expenses == (100 + 200 + 300 + 500) / 12
    assert no_incomes.cut_sum == (200 + 500) / 12


def test_div_method(no_incomes_data_class):
    # Arrange
    no_incomes = NoIncomes(no_incomes_data_class)

    # Act
    result1 = no_incomes._div(10, 2)
    result2 = no_incomes._div(10, 0)

    # Assert
    assert result1 == 5
    assert result2 == 0
