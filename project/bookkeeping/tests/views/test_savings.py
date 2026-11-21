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
    FIGURE,
    GROUP_FIGURE,
    KINDS,
    PANEL_TITLE,
    cell_texts,
    closed_every_other,
    fund_with_a_sell,
    quiet_build,
    row_cells,
    row_tags,
    row_titles,
    stale_fund,
    switch_a_into_b,
    tab_cards,
    tab_table,
    table_titled,
    total_cells,
    view_queries,
)
from ..signals.helpers import buy, sell, worth

pytestmark = pytest.mark.django_db

FUNDS_TAB = "bookkeeping:tab_funds"


def _table(client, title="Fondai"):
    return tab_table(client, FUNDS_TAB, title)


def _fondai(client):
    return tab_fragment(client, reverse(FUNDS_TAB))


@pytest.mark.parametrize(
    "title, rows",
    [
        pytest.param("Fondai", ["FFF"], id="funds"),
        # the funds of kind Pensijos first, then the II pillar's Pension funds
        pytest.param("Pensijos", ["PPP", "PensionType"], id="pensions"),
    ],
)
def test_each_table_lists_its_own_funds(client_logged, main_user, title, rows):
    with quiet_build(main_user):
        SavingFactory(saving_type=SavingTypeFactory(title="FFF", type="funds"))
        SavingFactory(saving_type=SavingTypeFactory(title="PPP", type="pensions"))
        PensionFactory()

    assert row_titles(_table(client_logged, title)) == rows


INCOME = (1999, 10000)


# ink at any share, one decimal: the invested price, not its fee, over the year's
# incomes; a year with no incomes draws the Card empty, though the next year has some
@pytest.mark.parametrize(
    "income, savings, card",
    [
        pytest.param(INCOME, [], ("0,0%", "neutral"), id="0"),
        pytest.param(INCOME, [(500, 0, "account")], ("5,0%", "neutral"), id="5"),
        pytest.param(INCOME, [(2049, 0, "account")], ("20,5%", "neutral"), id="20"),
        pytest.param(
            (1999, 10),
            [(20, 0, "account")],
            ("200,0%", "neutral"),
            id="over-the-incomes",
        ),
        *(
            pytest.param(INCOME, [(2000, 500, source)], ("20,0%", "neutral"), id=source)
            for source in SavingType.FeeSource.values
        ),
        pytest.param(
            (2000, 10000), [(2049, 0, "account")], ("&mdash;", "empty"), id="no-incomes"
        ),
    ],
)
def test_saved_share_card_is_the_year_s_savings_over_its_incomes_in_ink(
    client_logged, main_user, income, savings, card
):
    year, price = income
    with quiet_build(main_user):
        IncomeFactory(date=date(year, 1, 1), price=price)
        for saved, fee, fee_source in savings:
            SavingFactory(
                price=saved,
                fee=fee,
                saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
            )

    content = _fondai(client_logged)
    figures = [
        (label, figure, state) for label, figure, _note, state in tab_cards(content)
    ]
    alerts = re.findall(r'class="alert ([^"]*)"', content)

    assert (figures[:1], alerts) == (
        [("Pajamų dalis pervedama taupymui", *card)],
        [],
    )


def _fund(bought, worth_price):
    """A seed: a fund bought for `bought` and worth `worth_price` at the year end."""

    def seed():
        fund = SavingTypeFactory(title="Fund")
        buy(fund, bought)
        worth(fund, worth_price)

    return seed


# 300,60 of profit, 30,06 %
_gaining_fund = _fund(100000, 130060)


def _gaining_pension():
    """Bought 600,00, worth 700,00: 100,00 of profit, 16,67 %."""
    pension = PensionTypeFactory(title="Pension")
    PensionFactory(pension_type=pension, price=60000, fee=0)
    PensionWorthFactory(pension_type=pension, price=70000)


FUND_PROFIT = ("Fondų pelnas", "301", "30,1%", "neutral")
PENSION_PROFIT = ("Pensijų pelnas", "100", "16,7%", "neutral")
NO_FUND_PROFIT = ("Fondų pelnas", "&mdash;", "", "empty")
NO_PENSION_PROFIT = ("Pensijų pelnas", "&mdash;", "", "empty")


@pytest.mark.parametrize(
    "seeds, cards, tables",
    [
        pytest.param(
            [_gaining_fund, _gaining_pension],
            [FUND_PROFIT, PENSION_PROFIT],
            ["Fondai", "Pensijos"],
            id="both",
        ),
        pytest.param(
            [_gaining_fund],
            [FUND_PROFIT, NO_PENSION_PROFIT],
            ["Fondai"],
            id="no-pensions",
        ),
        pytest.param(
            [_gaining_pension],
            [NO_FUND_PROFIT, PENSION_PROFIT],
            ["Pensijos"],
            id="no-funds",
        ),
        pytest.param([], [NO_FUND_PROFIT, NO_PENSION_PROFIT], [], id="neither"),
        # a table with rows but no profit draws its Card empty too (Q45)
        pytest.param(
            [_fund(100000, 100000), _gaining_pension],
            [NO_FUND_PROFIT, PENSION_PROFIT],
            ["Fondai", "Pensijos"],
            id="zero-profit",
        ),
        pytest.param(
            [_fund(100000, 70000)],
            [("Fondų pelnas", "-300", "-30,0%", "neutral"), NO_PENSION_PROFIT],
            ["Fondai"],
            id="loss",
        ),
        # under 0,50 either way the figure keeps its cents, never a "0", and its note
        # its one decimal, "0,0%" too (Q47, Q66); from 0,50 whole euros
        *(
            pytest.param(
                [_fund(bought, worth_price)],
                [("Fondų pelnas", *figure_note, "neutral"), NO_PENSION_PROFIT],
                ["Fondai"],
                id=case,
            )
            for case, bought, worth_price, figure_note in (
                ("cents", 1000, 1030, ("0,30", "3,0%")),
                ("cents-loss", 1000, 970, ("-0,30", "-3,0%")),
                ("cents-of-a-big-fund", 100000, 100030, ("0,30", "0,0%")),
                ("under-half-a-euro", 10000, 10049, ("0,49", "0,5%")),
                ("under-half-a-euro-loss", 10000, 9951, ("-0,49", "-0,5%")),
                ("half-a-euro", 10000, 10050, ("1", "0,5%")),
                ("half-a-euro-loss", 10000, 9950, ("-1", "-0,5%")),
            )
        ),
    ],
)
def test_profit_cards_read_each_table_s_total_and_a_table_without_one_draws_its_empty(
    client_logged, main_user, seeds, cards, tables
):
    with quiet_build(main_user):
        for seed in seeds:
            seed()

    content = _fondai(client_logged)
    drawn = re.findall(PANEL_TITLE, content)

    assert (tab_cards(content)[1:], drawn) == (cards, tables)


TABLES = [
    pytest.param("Fondai", SavingFactory, "Savings", id="funds"),
    pytest.param("Pensijos", PensionFactory, "PensionType", id="pensions"),
]


@pytest.mark.parametrize("title, factory, row", TABLES)
def test_table_shows_the_year_s_transfers_in_its_row_and_total(
    client_logged, main_user, title, factory, row
):
    with quiet_build(main_user):
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
    client_logged, main_user, title, factory, worth_factory, row
):
    with quiet_build(main_user):
        factory()
        worth_factory()
        worth_factory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    assert row_cells(_table(client_logged, title), row)[8] == "1999-01-01"


@pytest.mark.parametrize(
    "title, kind, bought, sold, fee, profit",
    [
        pytest.param(
            "Fondai",
            "funds",
            100000,
            60000,
            0,
            [("-400,00", "loss"), ("-40,00%", "loss")],
            id="funds",
        ),
        pytest.param(
            "Pensijos",
            "pensions",
            2596753,
            3459722,
            20000,
            [("8.429,69", "gain"), ("32,46%", "gain")],
            id="pensions",
        ),
    ],
)
def test_closed_fund_with_a_sell_shows_its_signed_profit_but_no_worth(
    client_logged, main_user, title, kind, bought, sold, fee, profit
):
    with quiet_build(main_user):
        fund_with_a_sell("Closed", bought, sold, fee=fee, kind=kind, closed=1999)

    cells = row_tags(_table(client_logged, title), "Closed")

    assert [text for _attrs, text in cells[8:10]] == ["-", "-"]
    assert [
        (text, re.search(r'data-sign="(\w+)"', attrs).group(1))
        for attrs, text in cells[10:12]
    ] == profit
    assert not re.search(r"table-(success|danger)", str(cells))


@pytest.mark.parametrize("title, kind", KINDS)
@pytest.mark.parametrize("sold", [True, False])
def test_open_fund_with_no_worth_draws_its_cost_and_its_worth_cells_empty(
    client_logged, main_user, title, kind, sold
):
    with quiet_build(main_user):
        if sold:
            fund_with_a_sell("Open", 100000, 60000, kind=kind)
        else:
            buy(SavingTypeFactory(title="Open", type=kind), 100000)

    cells = row_tags(_table(client_logged, title), "Open")

    assert [
        (text, 'data-cell="empty"' in attrs) for attrs, text in [cells[4], *cells[8:]]
    ] == [("1.000,00", False), *[("-", True)] * 4]


def test_a_fund_worth_its_cost_draws_its_profit_and_total_as_an_empty_zero(
    client_logged, main_user
):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Even")
        buy(fund, 100000)
        worth(fund, 100000)

    table = _table(client_logged)
    row = re.search(r"<tr>\s*<td[^>]*>Even</td>(.*?)</tr>", table, re.S).group(1)

    foot = re.search(r"<tfoot>(.*?)</tfoot>", table, re.S).group(1)

    assert {
        "row": re.findall(r"<td([^>]*)>[^<]*</td>", row)[-2:],
        "total": re.findall(r"<td([^>]*)>[^<]*</td>", foot)[-2:],
    } == dict.fromkeys(
        ("row", "total"),
        [f'{GROUP_FIGURE} data-cell="empty"', f'{FIGURE} data-cell="empty"'],
    )


def _shape(table):
    """The attributes of each cell: per header row, the row, the foot row."""
    head = re.search(r"<thead>(.*?)</thead>", table, re.S).group(1)
    body = re.search(r"<tbody>(.*?)</tbody>", table, re.S).group(1)
    foot = re.search(r"<tfoot>(.*?)</tfoot>", table, re.S).group(1)
    return {
        "head": [re.findall(r"<th([^>]*)>", row) for row in head.split("<tr>")[1:]],
        "row": re.findall(r"<td([^>]*)>", body),
        "foot": re.findall(r"<tr([^>]*)>", foot) + re.findall(r"<td([^>]*)>", foot),
    }


CENTRED = ' class="text-center"'
CENTRED_START = ' class="text-center main__group-start"'
START = ' class="main__group-start"'
NAME = ' class="text-left funds-table__name"'
# the three header rows: 13 columns under their groups
HEAD = [
    [
        f'{NAME} rowspan="2"',
        f' rowspan="2" colspan="2"{CENTRED_START}',
        f' colspan="2"{CENTRED_START}',
        f' colspan="4"{CENTRED_START}',
        f' rowspan="2" colspan="2"{CENTRED_START}',
        f' colspan="2" rowspan="2"{CENTRED_START}',
    ],
    [f' colspan="2"{CENTRED_START}'] * 2 + [f' colspan="2"{CENTRED}'],
    [NAME, START, "", START, "", START, "", "", "", START, "", START, ""],
]

EMPTY = f'{FIGURE} data-cell="empty"'
SHOWN = f'{FIGURE} data-cell=""'
GAIN = f'{FIGURE} data-sign="gain" data-cell=""'
EMPTY_START = f'{GROUP_FIGURE} data-cell="empty"'
SHOWN_START = f'{GROUP_FIGURE} data-cell=""'
GAIN_START = f'{GROUP_FIGURE} data-sign="gain" data-cell=""'
DATE_START = ' class="main__date main__group-start"'


def test_funds_table_draws_each_column(client_logged, main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000, fee=100, when=date(1998, 1, 1))
        buy(fund, 20000, fee=200)
        sell(fund, 30000, fee=400)
        worth(fund, 120000)

    paid = ["1.000,00", "1,00", "200,00", "2,00", "1.200,00", "3,00", "300,00", "4,00"]
    # bought 1 200,00 for 3,00 of fees, 300,00 sold, worth 1 200,00
    profit = ["1.200,00", "297,00", "24,75%"]
    assert cell_texts(_table(client_logged)) == [
        [
            "Fondai",
            "1999 pradžioje",
            "1999",
            "Viso",
            "Rinkos vertė",
            "Pelnas/Nuostolis",
        ],
        ["Pervesta", "Pervesta", "Parduota"],
        ["Fondas", *["Suma", "Mokesčiai"] * 4, "Data", "Suma", "Suma", "%"],
        ["Fund", *paid, "1999-12-31", *profit],
        ["Viso", *paid, *profit],
    ]


def test_funds_tables_cells_carry_their_spans_and_states(client_logged, main_user):
    # bought in the year, the fund worth more than it cost; the pension has no worth
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 130000)
        PensionFactory(price=60000, fee=0)

    content = _fondai(client_logged)
    shapes = [_shape(table_titled(content, title)) for title in ("Fondai", "Pensijos")]

    # start, its fee; the year, its fee; the total in, its fee, sold, its fee
    paid = [EMPTY_START, EMPTY, SHOWN_START, EMPTY, SHOWN_START, EMPTY, EMPTY, EMPTY]
    assert shapes == [
        {
            "head": HEAD,
            "row": [NAME, *paid, DATE_START, SHOWN, GAIN_START, GAIN],
            "foot": [
                ' class="main__total"',
                NAME,
                *paid,
                f' colspan="2"{SHOWN_START}',
                GAIN_START,
                GAIN,
            ],
        },
        {
            "head": HEAD,
            "row": [
                NAME,
                *paid,
                f'{DATE_START} data-cell="empty"',
                EMPTY,
                EMPTY_START,
                EMPTY,
            ],
            "foot": [
                ' class="main__total"',
                NAME,
                *paid,
                f' colspan="2"{EMPTY_START}',
                EMPTY_START,
                EMPTY,
            ],
        },
    ]


def _funds_closed_every_other(i, kind):
    fund_with_a_sell(
        f"Fund {i}", 100000, 60000, kind=kind, closed=closed_every_other(i)
    )
    PensionFactory(pension_type=PensionTypeFactory(title=f"P {i}"))


def _switches(i, kind):
    a = fund_with_a_sell(f"A {i}", 100000, 60000, kind=kind)
    b = SavingTypeFactory(title=f"B {i}", type=kind)
    SavingChangeFactory(
        from_account=a, to_account=b, price=1000, fee=0, date=date(1999, 7, 1)
    )


def _a_stale_fund(i, kind):
    stale_fund(f"Fund {i}", kind)


@pytest.mark.parametrize(
    "build",
    [_funds_closed_every_other, _switches, _a_stale_fund],
    ids=["closed", "switches", "stale"],
)
@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_funds_tab_queries_do_not_grow(client_logged, main_user, build, kind):
    queries = [
        view_queries(client_logged, main_user, FUNDS_TAB, lambda i: build(i, kind), n)
        for n in (2, 4)
    ]

    assert queries[0] == queries[1]


@pytest.mark.parametrize(
    "title, kind", [*KINDS, pytest.param("Fondai", "shares", id="shares")]
)
def test_total_counts_the_switched_money_once(client_logged, main_user, title, kind):
    with quiet_build(main_user):
        switch_a_into_b(kind=kind)

    cells = total_cells(_table(client_logged, title))

    # the total in, and the profit's percent on that base
    assert (cells[5], cells[-1]) == ("2.300,00", "7,69%")


def _source_closed_before_the_year():
    """B's total keeps the base A switched into it before A closed: 100,00 on 1 300,00."""
    a = SavingTypeFactory(title="A", closed=1998)
    b = SavingTypeFactory(title="B")
    buy(a, 100000, when=date(1998, 1, 1))
    SavingChangeFactory(
        from_account=a, to_account=b, price=130000, fee=0, date=date(1998, 6, 1)
    )
    worth(b, 140000)


def _switched_through_a_closed_fund():
    a = SavingTypeFactory(title="A")
    b = SavingTypeFactory(title="B", closed=1998)
    c = SavingTypeFactory(title="C")
    buy(a, 100000, when=date(1998, 1, 1))
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
    buy(c, 100000, when=date(1998, 1, 1))
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
    buy(fund, 100000)
    worth(fund, 130000)


@pytest.mark.parametrize(
    "build, percent",
    [
        pytest.param(_switched_through_a_closed_fund, "10,00%", id="through-closed"),
        pytest.param(_gain_passed_on_by_a_closed_fund, "15,00%", id="gain-passed-on"),
        pytest.param(_no_switches, "30,00%", id="no-switches"),
        pytest.param(_source_closed_before_the_year, "7,69%", id="closed-source"),
    ],
)
def test_total_profit_percentage(client_logged, main_user, build, percent):
    with quiet_build(main_user):
        build()

    assert total_cells(_table(client_logged))[-1] == percent


def test_pensions_total_ignores_a_switch_between_funds(client_logged, main_user):
    with quiet_build(main_user):
        switch_a_into_b(kind="funds")
        PensionFactory(price=100000)
        PensionWorthFactory(price=130000)

    table = _table(client_logged, "Pensijos")

    assert total_cells(table)[5] == "1.000,00"
    assert total_cells(table)[-1] == row_cells(table, "PensionType")[-1]
