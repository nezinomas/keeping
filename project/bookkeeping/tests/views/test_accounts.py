import re

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory
from ....savings.tests.factories import SavingFactory
from .. import factories
from ..helper import tab_table

pytestmark = pytest.mark.django_db

OVERVIEW = "bookkeeping:tab_overview"
FUNDS = "bookkeeping:tab_funds"
FUNDS_HEADER = (
    r'<th rowspan="2" colspan="2" class="[^"]*">1999 pradžioje</th>\s*'
    r'<th colspan="2" class="[^"]*">1999</th>'
)


@pytest.mark.parametrize(
    "url_name, title, factory, header",
    [
        pytest.param(
            OVERVIEW,
            "Sąskaitos",
            factories.AccountWorthFactory,
            r"<th>1999 pradžioje</th>",
            id="accounts",
        ),
        pytest.param(FUNDS, "Fondai", SavingFactory, FUNDS_HEADER, id="funds"),
        pytest.param(FUNDS, "Pensijos", PensionFactory, FUNDS_HEADER, id="pensions"),
    ],
)
def test_header_reads_the_selected_year(
    client_logged, url_name, title, factory, header
):
    factory()

    assert re.search(header, tab_table(client_logged, url_name, title))


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


@pytest.mark.parametrize(
    "url_name, title, factory, kind",
    [
        pytest.param(
            OVERVIEW,
            "Sąskaitos",
            factories.AccountWorthFactory,
            "accounts",
            id="accounts",
        ),
        pytest.param(FUNDS, "Fondai", SavingFactory, "savings", id="funds"),
        pytest.param(FUNDS, "Pensijos", PensionFactory, "pensions", id="pensions"),
    ],
)
def test_each_table_refreshes_its_own_balances(
    client_logged, url_name, title, factory, kind
):
    factory()

    table = tab_table(client_logged, url_name, title)
    url = reverse("bookkeeping:regenerate_balances")

    assert re.search(
        r'<span class="tip right" data-tip="Bus atnaujinti tik šios lentelės '
        rf'balansai.">\s*<a href="#" role="button" hx-get="{url}\?type={kind}">',
        table,
    )
