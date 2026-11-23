import re
from datetime import date, datetime
from functools import partial

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
    FUNDS_TAB,
    GROUP_FIGURE,
    KINDS,
    PANEL_TITLE,
    cell_texts,
    closed_every_other,
    fund_with_a_sell,
    funds_table,
    quiet_build,
    row_cells,
    row_tags,
    row_titles,
    signed_cells,
    stale_fund,
    switch_a_into_b,
    tab_cards,
    table_titled,
    total_cells,
    total_tags,
    view_queries,
)
from ..signals.helpers import buy, sell, worth

pytestmark = pytest.mark.django_db


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

    assert row_titles(funds_table(client_logged, title)) == rows


INCOME = (1999, 10000)


# ink at any share: every Fund kind's invested price, not the II pillar, over the year's
# incomes, its sum the note; no incomes: an empty Card, its note only with Savings
@pytest.mark.parametrize(
    "income, savings, card",
    [
        pytest.param(INCOME, [], ("0,0%", "0,00 €", "neutral"), id="0"),
        pytest.param(
            (1999, 10), [], ("0,0%", "0,00 €", "neutral"), id="0-of-small-incomes"
        ),
        pytest.param(
            INCOME,
            [(500, 0, "account", "funds")],
            ("5,0%", "5,00 €", "neutral"),
            id="5",
        ),
        pytest.param(
            INCOME,
            [(2049, 0, "account", "funds")],
            ("20,5%", "20,49 €", "neutral"),
            id="20",
        ),
        pytest.param(
            (1999, 10),
            [(20, 0, "account", "funds")],
            ("200,0%", "0,20 €", "neutral"),
            id="over-the-incomes",
        ),
        *(
            pytest.param(
                INCOME,
                [(2000, 500, source, "funds")],
                ("20,0%", "20,00 €", "neutral"),
                id=source,
            )
            for source in SavingType.FeeSource.values
        ),
        pytest.param(
            (1999, 1000000),
            [
                (123456, 0, "account", "funds"),
                (500, 0, "account", "shares"),
                (500, 0, "account", "pensions"),
            ],
            ("12,4%", "1.244,56 €", "neutral"),
            id="every-fund-kind",
        ),
        pytest.param(
            (2000, 10000),
            [(2049, 0, "account", "funds")],
            ("&mdash;", "20,49 €", "empty"),
            id="no-incomes",
        ),
        # neither Savings nor incomes: the empty Card carries no note (Q274)
        pytest.param((2000, 10000), [], ("&mdash;", "", "empty"), id="neither"),
    ],
)
def test_saved_share_card_reads_the_savings_share_and_sum_or_draws_empty(
    client_logged, main_user, income, savings, card
):
    year, price = income
    with quiet_build(main_user):
        IncomeFactory(date=date(year, 1, 1), price=price)
        PensionFactory(date=date(1999, 1, 1), price=7000, fee=0)
        # another year's Savings count in neither the share nor its note
        buy(SavingTypeFactory(title="Earlier"), 9800, when=date(1998, 1, 1))
        buy(SavingTypeFactory(title="Later"), 9900, when=date(2000, 1, 1))
        for saved, fee, fee_source, kind in savings:
            SavingFactory(
                price=saved,
                fee=fee,
                saving_type=SavingTypeFactory(
                    title=f"Fund {kind}", fee_source=fee_source, type=kind
                ),
            )

    content = _fondai(client_logged)
    alerts = re.findall(r'class="alert ([^"]*)"', content)

    assert (tab_cards(content)[:1], alerts) == (
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

    assert row_cells(funds_table(client_logged, title), row)[8] == "1999-01-01"


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

    cells = row_tags(funds_table(client_logged, title), "Closed")

    assert [text for _attrs, text in cells[8:10]] == ["-", "-"]
    assert signed_cells(cells[10:12]) == profit


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

    cells = row_tags(funds_table(client_logged, title), "Open")

    assert [
        (text, 'data-cell="empty"' in attrs) for attrs, text in [cells[4], *cells[8:]]
    ] == [("1.000,00", False), *[("-", True)] * 4]


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
NAME = ' class="funds-table__name"'
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
LOSS_START = f'{GROUP_FIGURE} data-sign="loss" data-cell=""'
DATE_START = ' class="main__date main__group-start"'


def _bought_sold_and_worth():
    """Bought 1 200,00 for 3,00 of fees, 300,00 sold for 4,00, worth 1 200,00."""
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000, fee=100, when=date(1998, 1, 1))
    buy(fund, 20000, fee=200)
    sell(fund, 30000, fee=400)
    worth(fund, 120000)


PAID = ["1.000,00", "1,00", "200,00", "2,00", "1.200,00", "3,00", "300,00", "4,00"]
PROFIT = ["1.200,00", "297,00", "24,75%"]
PENSION_PAID = ["-", "-", "6,60", "-", "6,60", "-", "-", "-"]


# each table's heads, its row and its total; the name column headed by what it lists
@pytest.mark.parametrize(
    "title, seed, name, rows",
    [
        pytest.param(
            "Fondai",
            _bought_sold_and_worth,
            "Fondas",
            [["Fund", *PAID, "1999-12-31", *PROFIT], ["Viso", *PAID, *PROFIT]],
            id="funds",
        ),
        pytest.param(
            "Pensijos",
            lambda: PensionFactory(price=660, fee=0),
            "Pensijų fondas",
            [
                ["PensionType", *PENSION_PAID, "-", "-", "-", "-"],
                ["Viso", *PENSION_PAID, "-", "-", "0%"],
            ],
            id="pensions",
        ),
    ],
)
def test_funds_and_pensions_tables_draw_each_column(
    client_logged, main_user, title, seed, name, rows
):
    with quiet_build(main_user):
        seed()

    assert cell_texts(funds_table(client_logged, title)) == [
        [
            title,
            "1999 pradžioje",
            "1999",
            "Viso",
            "Rinkos vertė",
            "Pelnas/Nuostolis",
        ],
        ["Pervesta", "Pervesta", "Parduota"],
        [name, *["Suma", "Mokesčiai"] * 4, "Data", "Suma", "Suma", "%"],
        *rows,
    ]


# the profit and its percent, row and total: two decimals and the sign; an even fund
# a dash and an empty 0% (Q216); a percent rounding to 0, or with no cost, a shown 0%
@pytest.mark.parametrize(
    "bought, worth_of, profit",
    [
        pytest.param(
            100000, 101500, [(GAIN_START, "15,00"), (GAIN, "1,50%")], id="1.5"
        ),
        pytest.param(
            1000000, 1000400, [(GAIN_START, "4,00"), (GAIN, "0,04%")], id="0.04"
        ),
        pytest.param(
            1000000, 999960, [(LOSS_START, "-0,40"), (SHOWN, "0%")], id="rounded"
        ),
        pytest.param(0, 50000, [(GAIN_START, "500,00"), (SHOWN, "0%")], id="no-cost"),
        pytest.param(100000, 100000, [(EMPTY_START, "-"), (EMPTY, "0%")], id="even"),
    ],
)
def test_a_profit_and_its_percent_read_signed_shown_or_empty(
    client_logged, main_user, bought, worth_of, profit
):
    with quiet_build(main_user):
        _fund(bought, worth_of)()

    table = funds_table(client_logged)

    assert {
        "row": row_tags(table, "Fund")[-2:],
        "total": total_tags(table)[-2:],
    } == dict.fromkeys(("row", "total"), profit)


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


# 2 items against 4: a switch makes two funds, so its counts are of 4 and 8
@pytest.mark.parametrize(
    "build, counts",
    [
        pytest.param(_funds_closed_every_other, (2, 4), id="closed"),
        pytest.param(_switches, (4, 8), id="switches"),
        pytest.param(_a_stale_fund, (2, 4), id="stale"),
    ],
)
@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_funds_tab_queries_do_not_grow(client_logged, main_user, build, counts, kind):
    queries = [
        view_queries(client_logged, main_user, FUNDS_TAB, lambda i: build(i, kind), n)
        for n in counts
    ]

    assert queries[0] == queries[1]


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


@pytest.mark.parametrize(
    "seed, title, total",
    [
        *(
            pytest.param(
                partial(switch_a_into_b, kind=kind, **switch),
                title,
                total,
                id=f"{year}-{kind}",
            )
            for title, kind in (
                ("Fondai", "funds"),
                ("Pensijos", "pensions"),
                ("Fondai", "shares"),
            )
            for year, switch, total in (
                ("1999", {"a_zeroed": True}, ("2.300,00", "7,69%")),
                # a switch in the year after the check counts nothing in 1999
                (
                    "2000",
                    {"checked": date(1999, 12, 31), "on": date(2000, 6, 1)},
                    ("1.000,00", "30,00%"),
                ),
            )
        ),
        pytest.param(
            _switched_through_a_closed_fund,
            "Fondai",
            ("1.500,00", "10,00%"),
            id="through-closed",
        ),
        pytest.param(
            _gain_passed_on_by_a_closed_fund,
            "Fondai",
            ("1.500,00", "15,00%"),
            id="gain-passed-on",
        ),
        pytest.param(
            _source_closed_before_the_year,
            "Fondai",
            ("1.300,00", "7,69%"),
            id="closed-source",
        ),
    ],
)
def test_total_counts_the_money_switched_by_the_year_once(
    client_logged, main_user, seed, title, total
):
    with quiet_build(main_user):
        seed()

    cells = total_cells(funds_table(client_logged, title))

    # the total in, and the profit's percent on that base
    assert (cells[5], cells[-1]) == total


def test_pensions_total_ignores_a_switch_between_funds(client_logged, main_user):
    with quiet_build(main_user):
        switch_a_into_b(a_zeroed=True)
        PensionFactory(price=100000)
        PensionWorthFactory(price=130000)

    table = funds_table(client_logged, "Pensijos")

    assert total_cells(table)[5] == "1.000,00"
    assert total_cells(table)[-1] == row_cells(table, "PensionType")[-1]
