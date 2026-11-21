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
from ..helper import PANEL_TITLE, quiet_build, row_cells, stale_fund
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db


def _mark(main_user, titles, savings=False):
    """The journal marks a new expense type per title unnecessary; its types."""
    j = JournalFactory()
    with quiet_build(main_user):
        types = [ExpenseTypeFactory(title=title) for title in titles]
        j.unnecessary_savings = savings
        j.unnecessary_expenses = json.dumps([t.pk for t in types])
        j.save()
    return types


def _cut(expense_type, main_user, price=120000):
    with quiet_build(main_user):
        ExpenseFactory(expense_type=expense_type, price=price, date=date(1999, 5, 1))


@pytest.fixture(name="unnecessary")
def fixture_unnecessary(main_user):
    with quiet_build(main_user):
        SavingTypeFactory()
    cut, _ = _mark(main_user, ["XXX", "YYY"], savings=True)
    _cut(cut, main_user)


HINT = (
    r'<span class="hint tip bottom" tabindex="0" data-tip="Nebūtinos išlaidos[^"]*"'
    r' aria-label="([^"]*)" aria-description="[^"]*">'
    r'<i class="bi bi-question-circle"></i></span>'
)
CUTS = "Nebūtinos išlaidos, kurių galima atsisakyti"


def _marks_nothing(main_user):
    pass


def _marks_a_type_never_spent_on(main_user):
    _mark(main_user, ["XXX"])


def _cuts_an_expense(main_user):
    _cut(*_mark(main_user, ["XXX"]), main_user)


def _cuts_a_cent(main_user):
    _cut(*_mark(main_user, ["XXX"]), main_user, price=1)


# the six whole months before the view's today hold the cut expense: 1.200,00 / 6;
# a cent over six months is a cut that rounds to 0, drawn "0", not "–" (Q193)
@time_machine.travel("1999-06-15")
@pytest.mark.parametrize(
    "journal, figure, hints",
    [
        pytest.param(_marks_nothing, "–", [], id="nothing-marked"),
        pytest.param(_marks_a_type_never_spent_on, "–", [CUTS], id="nothing-cut"),
        pytest.param(_cuts_an_expense, "200", [CUTS], id="a-cut"),
        pytest.param(_cuts_a_cent, "0", [CUTS], id="a-cut-rounding-to-0"),
    ],
)
def test_no_incomes_head_reads_its_label_its_muted_cut_and_a_hint(
    client_logged, main_user, journal, figure, hints
):
    journal(main_user)

    content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))
    heads = re.findall(
        PANEL_TITLE
        + r'<div class="table-responsive">\s*'
        + r"<table\b[^>]*>\s*<thead>\s*<tr>\s*"
        + r'<th class="text-left">(.*?)</th>',
        content,
        re.S,
    )

    # the label and the figure outside the tip; only the "?" opens one
    assert [
        (
            re.findall(r"^([^<]*?) <span", head),
            re.findall(
                r'<span class="main__figure main__figure--muted">([^<]*)<', head
            ),
            re.findall(r'class="([^"]*\btip\b[^"]*)"', head),
            re.findall(HINT, head),
        )
        for title, head in heads
        if title == "Be pajamų"
    ] == [(["Nebūtinos išlaidos"], [figure], ["hint tip bottom"] * len(hints), hints)]


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
    tips = re.findall(
        r'<span class="hint tip bottom" tabindex="0" data-tip="(Nebūtinos išlaidos[^"]*)"'
        r' aria-label="[^"]*" aria-description="([^"]*)">',
        content,
    )

    # the bubble's lines, and the one sentence a screen reader is given
    assert [(tip.splitlines(), said) for tip, said in tips] == [
        (
            [
                "Nebūtinos išlaidos, kurių galima atsisakyti:",
                "- XXX",
                "- YYY",
                "- Taupymas",
            ],
            "Nebūtinos išlaidos, kurių galima atsisakyti: XXX, YYY, Taupymas",
        )
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
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fresh", type=kind)
        buy(fund, 100000)
        worth(fund, 70000, month=3, day=1)

    actual = no_incomes.load_service(main_user, 1999, date(1999, 6, 1))["no_incomes"][0]

    assert actual["money_fund"] == money_fund
    assert actual["money_fund_pension"] == -30000


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_a_stale_worth_counts_as_zero(main_user, kind):
    with quiet_build(main_user):
        stale_fund(kind=kind)

    account_sum = AccountBalance.objects.filter(year=1999).aggregate(
        Sum("balance", default=0)
    )["balance__sum"]

    actual = no_incomes.load_service(main_user, 1999, date(1999, 6, 1))["no_incomes"][0]

    assert actual["money_fund"] == account_sum
    assert actual["money_fund_pension"] == account_sum
