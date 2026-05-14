import json
from pathlib import Path

import pytest
from django.template import Context, Template
from django.urls import resolve, reverse

from ....expenses.tests.factories import ExpenseTypeFactory
from ....journals.tests.factories import JournalFactory
from ....savings.tests.factories import SavingTypeFactory
from ... import views

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                        NoIncomes View
# -------------------------------------------------------------------------------------
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

    assert "Nebūtinos išlaidos, kurių galima atsisakyti:" in actual

    assert "- XXX" in actual
    assert "- YYY" in actual
    assert "- Taupymas" in actual


def test_template_month_value():
    with open(
        Path(__file__).cwd()
        / "project/bookkeeping/templates/bookkeeping/includes/no_incomes.html"
    ) as f:
        template = Template(f.read())

    ctx = Context(
        {
            "no_incomes": [
                {
                    "title": "x",
                    "money_fund": 11,
                    "money_fund_pension": 22,
                    "price": True,
                },
                {
                    "title": "y",
                    "money_fund": 33,
                    "money_fund_pension": 44,
                    "price": False,
                },
            ],
        }
    )
    actual = template.render(ctx)

    # price
    assert "0,11" in actual
    assert "0,22" in actual

    # month
    assert "33,0" in actual
    assert "44,0" in actual
