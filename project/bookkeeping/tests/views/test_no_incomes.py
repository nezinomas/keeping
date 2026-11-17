import json
import re
from datetime import date

import pytest
import time_machine
from django.db.models import Sum
from django.template.loader import render_to_string
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....core.tests.utils import tab_fragment
from ....expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ....journals.tests.factories import JournalFactory
from ....savings.tests.factories import SavingTypeFactory
from ...lib import no_incomes
from ..helper import row_cells, stale_fund
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db


@pytest.fixture(name="unnecessary")
def fixture_unnecessary():
    j = JournalFactory()
    e1 = ExpenseTypeFactory(title="XXX")
    e2 = ExpenseTypeFactory(title="YYY")
    SavingTypeFactory()

    j.unnecessary_savings = True
    j.unnecessary_expenses = json.dumps([e1.pk, e2.pk])
    j.save()
    ExpenseFactory(expense_type=e1, price=120000, date=date(1999, 5, 1))


# the six whole months before the view's today hold the cut expense: 1.200,00 / 6
@time_machine.travel("1999-06-15")
def test_no_incomes_head_names_its_figure_under_the_panel_title(
    client_logged, unnecessary
):
    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))

    assert re.findall(
        r'<h2 class="panel__title">([^<]*)</h2>\s*<div class="table-responsive">\s*'
        r"<table\b[^>]*>\s*<thead>\s*<tr>\s*<th[^>]*><span[^>]*>([^<]*)</span>",
        content,
    ) == [("Be pajamų", "Nebūtinos išlaidos 200")]


def test_no_incomes_panel_keeps_its_legend_under_the_table(client_logged):
    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))

    legend = re.findall(
        r'<h2 class="panel__title">Be pajamų</h2>.*?</table>\s*</div>\s*'
        r'<p class="mt-3">(.*?)</p>\s*</section>',
        content,
        re.S,
    )

    assert [
        re.sub(r"<[^>]+>|\s+", " ", line).split() for line in legend[0].split("<br>")
    ] == [
        ["€", "-", "Sąskaitose", "esantys", "pinigai"],
        ["F", "-", "Fondai/Akcijos"],
        ["P", "-", "Pensijų", "fondai"],
    ]


def test_no_incomes_tip_lists_the_unnecessary_expenses(client_logged, unnecessary):
    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))
    tip = re.search(
        r'<span class="tip[^"]*" data-tip="(Nebūtinos išlaidos[^"]*)"', content
    ).group(1)

    assert tip.splitlines() == [
        "Nebūtinos išlaidos, kurių galima atsisakyti:",
        "- XXX",
        "- YYY",
        "- Taupymas",
    ]


def test_template_month_value():
    ctx = {
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
    actual = render_to_string("bookkeeping/includes/no_incomes.html", ctx)

    assert row_cells(actual, "x") == ["0,11", "0,22"]
    assert row_cells(actual, "y") == ["33,0", "44,0"]


# the buy leaves its account at -100000; the worth is 70000
@pytest.mark.parametrize(
    "kind, money_fund",
    [("funds", -30000), ("shares", -30000), ("pensions", -100000)],
)
def test_a_fresh_worth_counts_by_its_fund_type(main_user, kind, money_fund):
    fund = SavingTypeFactory(title="Fresh", type=kind)
    buy(fund, 100000)
    worth(fund, 70000, month=3, day=1)

    actual = no_incomes.load_service(main_user, 1999, date(1999, 6, 1))["no_incomes"][0]

    assert actual["money_fund"] == money_fund
    assert actual["money_fund_pension"] == -30000


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_a_stale_worth_counts_as_zero(main_user, kind):
    stale_fund(kind=kind)

    account_sum = AccountBalance.objects.filter(year=1999).aggregate(
        Sum("balance", default=0)
    )["balance__sum"]

    actual = no_incomes.load_service(main_user, 1999, date(1999, 6, 1))["no_incomes"][0]

    assert actual["money_fund"] == account_sum
    assert actual["money_fund_pension"] == account_sum
