import json
from types import SimpleNamespace

import pytest
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
        "Nebūtinos išlaidos, kurių galima atsisakyti:<br />- XXX<br />- YYY<br />- Taupymas"
        in actual
    )


# ---------------------------------------------------------------------------------------
#                                                                        NoIncomes Helper
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _data():
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
def test_no_incomes_avg_expenses(savings, unnecessary, months, expect, _data):
    _data.savings = savings
    _data.unnecessary = unnecessary
    _data.months = months
    obj = NoIncomes(_data)

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
def test_no_incomes_cut_sum(savings, unnecessary, months, expect, _data):
    _data.savings = savings
    _data.unnecessary = unnecessary
    _data.months = months
    obj = NoIncomes(_data)

    assert round(obj.cut_sum, 2) == expect


def test_no_incomes_summary(_data):
    _data.savings = {"sum": 2}
    _data.unnecessary = ["Z", "Taupymas"]

    actual = NoIncomes(_data).summary

    assert actual[0]["label"] == "money"
    assert actual[0]["money_fund"] == 6
    assert actual[0]["money_fund_pension"] == 7

    assert actual[1]["label"] == "no_cut"
    assert round(actual[1]["money_fund"], 2) == 4
    assert round(actual[1]["money_fund_pension"], 2) == 4.67

    assert actual[2]["label"] == "cut"
    assert round(actual[2]["money_fund"], 2) == 12
    assert round(actual[2]["money_fund_pension"], 2) == 14
