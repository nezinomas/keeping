import re
from datetime import date, datetime

import pytest
import pytz
from django.urls import reverse

from ....core.tests.utils import tab_fragment
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import (
    PensionFactory,
    PensionTypeFactory,
)
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ..factories import PensionWorthFactory, SavingWorthFactory
from ..helper import (
    closed_every_other,
    fund_with_a_sell,
    row_cells,
    row_titles,
    switch_a_into_b,
    tab_table,
    total_cells,
    view_queries,
)
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db

FUNDS_TAB = "bookkeeping:tab_funds"
SAVED_SHARE = re.compile(
    r'<div class="alert ([^"]*)">Pajamų dalis pervedama taupymui: <b>([^<]*)</b>%'
)


def _table(client, title="Fondai"):
    return tab_table(client, FUNDS_TAB, title)


def _saved_share(client):
    """(colour class, percent) of the Saved share."""
    return SAVED_SHARE.search(tab_fragment(client, reverse(FUNDS_TAB))).groups()


@pytest.mark.parametrize(
    "title, rows",
    [
        pytest.param("Fondai", ["FFF"], id="funds"),
        # the funds of kind Pensijos first, then the II pillar's Pension funds
        pytest.param("Pensijos", ["PPP", "PensionType"], id="pensions"),
    ],
)
def test_each_table_lists_its_own_funds(client_logged, title, rows):
    SavingFactory(saving_type=SavingTypeFactory(title="FFF", type="funds"))
    SavingFactory(saving_type=SavingTypeFactory(title="PPP", type="pensions"))
    PensionFactory()

    assert row_titles(_table(client_logged, title)) == rows


@pytest.mark.parametrize(
    "income, price, fee, fee_source, percent",
    [
        pytest.param(10, 20, 0, "account", "200,0", id="over-the-incomes"),
        *(
            pytest.param(10000, 2000, 500, source, "20,0", id=source)
            for source in SavingType.FeeSource.values
        ),
    ],
)
def test_saved_share_is_the_invested_price_over_the_incomes(
    client_logged, income, price, fee, fee_source, percent
):
    IncomeFactory(price=income)
    SavingFactory(
        price=price,
        fee=fee,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    assert _saved_share(client_logged)[1] == percent


@pytest.mark.parametrize(
    "income, savings, alert",
    [
        pytest.param(10, [1], "alert-success", id="green"),
        pytest.param(100, [1], "alert-warning", id="yellow"),
        pytest.param(10, [], "alert-danger", id="red"),
    ],
)
def test_saved_share_colour(client_logged, income, savings, alert):
    IncomeFactory(price=income)
    for price in savings:
        SavingFactory(price=price)

    assert _saved_share(client_logged)[0] == alert


TABLES = [
    pytest.param("Fondai", SavingFactory, "Savings", id="funds"),
    pytest.param("Pensijos", PensionFactory, "PensionType", id="pensions"),
]


@pytest.mark.parametrize("title, factory, row", TABLES)
def test_table_shows_the_year_s_transfers_in_its_row_and_total(
    client_logged, title, factory, row
):
    factory(price=660)

    table = _table(client_logged, title)

    assert row_cells(table, row)[2] == "6,60"
    assert total_cells(table)[3] == "6,60"


@pytest.mark.parametrize(
    "title, factory, worth_factory, row",
    [
        pytest.param(
            "Fondai", SavingFactory, SavingWorthFactory, "Savings", id="funds"
        ),
        pytest.param(
            "Pensijos",
            PensionFactory,
            PensionWorthFactory,
            "PensionType",
            id="pensions",
        ),
    ],
)
def test_table_dates_the_latest_check(
    client_logged, title, factory, worth_factory, row
):
    factory()
    worth_factory()
    worth_factory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    assert row_cells(_table(client_logged, title), row)[8] == "1999-01-01"


@pytest.mark.parametrize(
    "title, kind, bought, sold, fee, profit",
    [
        pytest.param(
            "Fondai", "funds", 100000, 60000, 0, ["-400,00", "-40,00%"], id="funds"
        ),
        pytest.param(
            "Pensijos",
            "pensions",
            2596753,
            3459722,
            20000,
            ["8.429,69", "32,46%"],
            id="pensions",
        ),
    ],
)
def test_closed_fund_with_a_sell_shows_its_profit_but_no_worth(
    client_logged, title, kind, bought, sold, fee, profit
):
    fund_with_a_sell("Closed", bought, sold, fee=fee, kind=kind, closed=1999)

    cells = row_cells(_table(client_logged, title), "Closed")

    assert cells[8:10] == ["-", "-"]
    assert cells[10:12] == profit


def test_fund_with_a_loss_marks_its_profit_cells_as_a_loss(client_logged):
    fund_with_a_sell("Closed", 100000, 60000, closed=1999)

    table = _table(client_logged)
    row = re.search(r"<tr>\s*<td[^>]*>Closed</td>(.*?)</tr>", table, re.S).group(1)
    lost = re.findall(r'<td[^>]*data-sign="loss"[^>]*>(.*?)</td>', row, re.S)

    assert lost == ["-400,00", "-40,00%"]
    assert "table-success" not in row
    assert "table-danger" not in row


@pytest.mark.parametrize(
    "title, kind",
    [
        pytest.param("Fondai", "funds", id="funds"),
        pytest.param("Pensijos", "pensions", id="pensions"),
    ],
)
@pytest.mark.parametrize("sold", [True, False])
def test_open_fund_with_no_worth_shows_dashes(client_logged, title, kind, sold):
    if sold:
        fund_with_a_sell("Open", 100000, 60000, kind=kind)
    else:
        SavingFactory(
            saving_type=SavingTypeFactory(title="Open", type=kind), price=100000
        )

    assert row_cells(_table(client_logged, title), "Open")[8:] == ["-"] * 4


def test_open_fund_with_no_worth_marks_its_empty_cells(client_logged):
    SavingFactory(saving_type=SavingTypeFactory(title="Open"), price=100000)

    table = _table(client_logged)
    row = re.search(r"<tr>\s*<td[^>]*>Open</td>(.*?)</tr>", table, re.S).group(1)
    cells = re.findall(r"<td([^>]*)>(.*?)</td>", row, re.S)

    assert cells[4][1].strip() == "1.000,00"
    assert 'data-cell="empty"' not in cells[4][0]
    assert all('data-cell="empty"' in attrs for attrs, _ in cells[8:])


def test_a_fund_worth_its_cost_draws_its_profit_and_total_as_an_empty_zero(
    client_logged,
):
    fund = SavingTypeFactory(title="Even")
    buy(fund, 100000)
    worth(fund, 100000)

    table = _table(client_logged)
    row = re.search(r"<tr>\s*<td[^>]*>Even</td>(.*?)</tr>", table, re.S).group(1)

    foot = re.search(r"<tfoot>(.*?)</tfoot>", table, re.S).group(1)

    assert {
        "row": re.findall(r"<td([^>]*)>[^<]*</td>", row)[-2:],
        "total": re.findall(r"<th([^>]*)>[^<]*</th>", foot)[-2:],
    } == dict.fromkeys(("row", "total"), [' data-cell="empty"'] * 2)


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_funds_tab_queries_do_not_grow_with_closed_funds(
    client_logged, main_user, kind
):
    def build(i):
        fund_with_a_sell(
            f"Fund {i}", 100000, 60000, kind=kind, closed=closed_every_other(i)
        )
        PensionFactory(pension_type=PensionTypeFactory(title=f"P {i}"))

    queries = [
        view_queries(client_logged, main_user, FUNDS_TAB, build, n) for n in (2, 4)
    ]

    assert queries[0] == queries[1]


@pytest.mark.parametrize(
    "title, kind",
    [
        pytest.param("Fondai", "funds", id="funds"),
        pytest.param("Fondai", "shares", id="shares"),
        pytest.param("Pensijos", "pensions", id="pensions"),
    ],
)
def test_total_counts_the_switched_money_once(client_logged, title, kind):
    switch_a_into_b(kind=kind)

    cells = total_cells(_table(client_logged, title))

    assert cells[5] == "2.300,00"
    assert cells[-1] == "7,69%"


def test_total_keeps_the_base_of_a_source_closed_before_the_year(client_logged):
    a = SavingTypeFactory(title="A", closed=1998)
    b = SavingTypeFactory(title="B")
    SavingFactory(saving_type=a, price=100000, date=date(1998, 1, 1))
    SavingChangeFactory(
        from_account=a, to_account=b, price=130000, fee=0, date=date(1998, 6, 1)
    )
    worth(b, 140000)

    table = _table(client_logged)

    assert total_cells(table)[-1] == row_cells(table, "B")[-1]


def _switched_through_a_closed_fund():
    a = SavingTypeFactory(title="A")
    b = SavingTypeFactory(title="B", closed=1998)
    c = SavingTypeFactory(title="C")
    SavingFactory(saving_type=a, price=100000, fee=0, date=date(1998, 1, 1))
    for source, target in ((a, b), (b, c)):
        SavingChangeFactory(
            from_account=source,
            to_account=target,
            price=50000,
            fee=0,
            date=date(1998, 6, 1),
        )
    worth(a, 50000)
    worth(c, 60000)


def _gain_passed_on_by_a_closed_fund():
    a = SavingTypeFactory(title="A", closed=1998)
    b = SavingTypeFactory(title="B")
    c = SavingTypeFactory(title="C")
    SavingFactory(saving_type=c, price=100000, fee=0, date=date(1998, 1, 1))
    for source, target, price in ((c, a, 40000), (a, b, 50000)):
        SavingChangeFactory(
            from_account=source,
            to_account=target,
            price=price,
            fee=0,
            date=date(1998, 6, 1),
        )
    worth(c, 70000)
    worth(b, 55000)


def _no_switches():
    fund = SavingTypeFactory(title="A")
    SavingFactory(saving_type=fund, price=100000, fee=0, date=date(1999, 1, 1))
    worth(fund, 130000)


@pytest.mark.parametrize(
    "build, percent",
    [
        pytest.param(_switched_through_a_closed_fund, "10,00%", id="through-closed"),
        pytest.param(_gain_passed_on_by_a_closed_fund, "15,00%", id="gain-passed-on"),
        pytest.param(_no_switches, "30,00%", id="no-switches"),
    ],
)
def test_total_profit_percentage(client_logged, build, percent):
    build()

    assert total_cells(_table(client_logged))[-1] == percent


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_funds_tab_queries_do_not_grow_with_switches(client_logged, main_user, kind):
    def build(i):
        a = fund_with_a_sell(f"A {i}", 100000, 60000, kind=kind)
        b = SavingTypeFactory(title=f"B {i}", type=kind)
        SavingChangeFactory(
            from_account=a, to_account=b, price=1000, fee=0, date=date(1999, 7, 1)
        )

    queries = [
        view_queries(client_logged, main_user, FUNDS_TAB, build, n) for n in (2, 4)
    ]

    assert queries[0] == queries[1]


def test_pensions_total_ignores_a_switch_between_funds(client_logged):
    switch_a_into_b(kind="funds")
    PensionFactory(price=100000)
    PensionWorthFactory(price=130000)

    table = _table(client_logged, "Pensijos")

    assert total_cells(table)[5] == "1.000,00"
    assert total_cells(table)[-1] == row_cells(table, "PensionType")[-1]
