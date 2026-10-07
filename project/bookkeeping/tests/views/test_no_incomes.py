import json
from datetime import date, datetime
from pathlib import Path

import pytest
import pytz
from django.db.models import Sum
from django.template import Context, Template
from django.urls import resolve, reverse

from ....accounts.models import AccountBalance
from ....expenses.tests.factories import ExpenseTypeFactory
from ....journals.tests.factories import JournalFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingCloseFactory
from ... import views
from ...lib import no_incomes
from ..factories import SavingWorthFactory

pytestmark = pytest.mark.django_db


# NoIncomes View
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


def _stale_fund(kind):
    fund = SavingTypeFactory(title="Stale", type=kind)
    SavingFactory(saving_type=fund, price=100000, fee=0, date=date(1999, 1, 1))
    SavingWorthFactory(
        saving_type=fund,
        price=100000,
        date=datetime(1999, 3, 1, 12, tzinfo=pytz.utc),
    )
    SavingCloseFactory(from_account=fund, price=40000, fee=0, date=date(1999, 6, 1))


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_a_stale_worth_counts_as_zero(main_user, kind):
    _stale_fund(kind)

    account_sum = AccountBalance.objects.filter(year=1999).aggregate(
        Sum("balance", default=0)
    )["balance__sum"]

    actual = no_incomes.load_service(main_user, 1999)["no_incomes"][0]

    assert actual["money_fund"] == account_sum
    assert actual["money_fund_pension"] == account_sum
