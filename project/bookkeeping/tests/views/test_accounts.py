import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import tab_fragment
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory
from ....savings.tests.factories import SavingFactory
from .. import factories
from ..helper import FUNDS_TAB, cell_texts, funds_table, tab_table, table_titled

pytestmark = pytest.mark.django_db

OVERVIEW = "bookkeeping:tab_overview"
FUNDS_HEADER = (
    r'<th rowspan="2" colspan="2" class="[^"]*">1999 pradžioje</th>\s*'
    r'<th colspan="2" class="[^"]*">1999</th>'
)


def test_header_reads_the_selected_year(client_logged):
    PensionFactory()

    assert re.search(FUNDS_HEADER, funds_table(client_logged, "Pensijos"))


def test_accounts_table_draws_each_column_under_a_left_title(client_logged):
    account = AccountFactory()
    IncomeFactory(account=account, date=date(1998, 1, 1), price=100000)
    IncomeFactory(account=account, price=50000)
    ExpenseFactory(account=account, price=20000)
    factories.AccountWorthFactory(account=account, price=125000)

    table = tab_table(client_logged, OVERVIEW, "Sąskaitos")
    first_cells = re.findall(r"<tr\b[^>]*>\s*<t[hd]([^>]*)>", table)

    assert (first_cells, cell_texts(table)) == (
        [' class="text-left"'] * 3,
        [
            [
                "Sąskaitos",
                "1999 pradžioje",
                "Pajamos",
                "Išlaidos",
                "Balansas",
                "Turiu",
                "Delta",
            ],
            [
                "Account1",
                "1.000,00",
                "500,00",
                "200,00",
                "1.300,00",
                "1.250,00",
                "-50,00",
            ],
            ["Viso", "1.000,00", "500,00", "200,00", "1.300,00", "1.250,00", "-50,00"],
        ],
    )


@pytest.mark.parametrize(
    "worth, deltas",
    [
        pytest.param(1500, [("gain", "5,00"), ("gain", "5,00")], id="gain"),
        pytest.param(500, [("loss", "-5,00"), ("loss", "-5,00")], id="loss"),
        # zero: "ok" on the account, the dash on the total
        pytest.param(1000, [("gain", "ok"), ("", "-")], id="zero"),
    ],
)
def test_delta_reads_the_worth_check_on_the_row_and_the_total(
    client_logged, worth, deltas
):
    account = AccountFactory()
    IncomeFactory(account=account, price=1000)
    factories.AccountWorthFactory(account=account, price=worth)

    table = tab_table(client_logged, OVERVIEW, "Sąskaitos")
    body = table.split("</thead>")[1]
    last_cells = re.findall(r"<t[dh]([^>]*)>([^<]*)</t[dh]>\s*</tr>", body)

    assert [
        ("".join(re.findall(r'data-sign="(\w+)"', attrs)), text)
        for attrs, text in last_cells
    ] == deltas


def test_every_table_refreshes_every_balance(client_logged):
    factories.AccountWorthFactory()
    SavingFactory()
    PensionFactory()
    url = reverse("bookkeeping:regenerate_balances")
    overview, funds = (
        tab_fragment(client_logged, reverse(url_name))
        for url_name in (OVERVIEW, FUNDS_TAB)
    )

    # the icon opens the title's header cell; a funds table's carries its name width.
    # Its own id per table: the tab's reload gives the focus back to that id
    icons = [
        re.findall(
            r'<th class="([^"]*)"[^>]*>\s*<span class="tip right"'
            r' data-tip="([^"]*)">\s*<(\w+) type="(\w+)" id="([^"]*)"'
            r' class="refresh-icon" hx-(\w+)="([^"]*)"[^>]*\baria-label="\2">'
            r'\s*<i class="bi bi-arrow-repeat me-1">',
            table_titled(content, title),
        )
        for content, title in (
            (overview, "Sąskaitos"),
            (funds, "Fondai"),
            (funds, "Pensijos"),
        )
    ]

    tip = "Bus atnaujinti visų metų balansai."
    named = ("funds-table__name", tip)
    assert icons == [
        [(*head, "button", "button", f"refresh-{kind}", "post", url)]
        for head, kind in (
            (("text-left", tip), "accounts"),
            (named, "savings"),
            (named, "pensions"),
        )
    ]
