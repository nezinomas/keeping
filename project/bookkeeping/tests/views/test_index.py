import re
from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import (
    count_queries,
    paper_page_parts,
    quick_add_pills,
    tab_fragment,
    view_for,
)
from ....debts.tests.factories import (
    BorrowFactory,
    BorrowReturnFactory,
    LendFactory,
    LendReturnFactory,
)
from ....expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingCloseFactory
from ...tabs import INDEX_TABS
from ...views import TabCharts, TabOverview
from ..factories import AccountWorthFactory
from ..helper import (
    BOXED_TABLE,
    FIGURE,
    GROUP_FIGURE,
    PANEL_TITLE,
    cell_texts,
    quiet_build,
    row_cells,
    script_json,
    table_titled,
    total_cells,
)
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db

CASH_FLOW_CELL = r'<td[^>]*data-check="[^"]*">'
YEAR_END = (
    '<td class="main__figure" data-sign="gain" data-cell="" data-check="{state}">'
)
ACCOUNTS_TOTAL = '<td class="main__figure" data-cell="" data-check="{state}">'


@pytest.mark.parametrize("tab", INDEX_TABS, ids=lambda tab: tab.name)
@pytest.mark.parametrize(
    "headers, whole",
    [({}, True), ({"HX-Request": "true"}, False)],
    ids=["page", "fragment"],
)
def test_an_index_tab_is_the_whole_paper_page_unless_htmx_asks(
    client_logged, tab, headers, whole
):
    content = client_logged.get(tab.url, headers=headers).content.decode()

    assert f"<title>1999 | {tab.title}</title>" in content
    assert paper_page_parts(content) == {
        "bundle": whole,
        "subnav": whole,
        "quick-add": whole,
        "sticky headers": False,
        "tab panel": whole,
    }


@pytest.mark.parametrize(
    "url",
    [
        *(pytest.param(lambda tab=tab: tab.url, id=tab.name) for tab in INDEX_TABS),
        pytest.param(lambda: reverse("bookkeeping:forecast"), id="forecast"),
    ],
)
def test_an_index_view_sends_the_anonymous_to_the_login(client, url):
    response = client.get(url())

    assert response.url == f"{reverse('users:login')}?next={url()}"


def _add_items(first, last):
    for i in range(first, last):
        IncomeFactory(income_type=IncomeTypeFactory(title=f"Type {i}"))
        ExpenseFactory(expense_type=ExpenseTypeFactory(title=f"Type {i}"))
        SavingFactory(saving_type=SavingTypeFactory(title=f"Type {i}"))
        PensionFactory(pension_type=PensionTypeFactory(title=f"Type {i}"))
        AccountFactory(title=f"Account {i}")
        BorrowFactory(name=f"Name {i}")
        LendFactory(name=f"Name {i}")


# Balansas' cap holds its one read of the accounts, the Cash-flow check's other side
QUERY_CAPS = {"overview": 23, "funds": 11, "balance": 16, "charts": 8}


@pytest.mark.parametrize("tab", INDEX_TABS, ids=lambda tab: tab.name)
def test_an_index_tab_queries_stay_under_its_cap_and_do_not_grow(
    client_logged, main_user, tab
):
    def queries():
        return count_queries(lambda: client_logged.get(tab.url))

    with quiet_build(main_user):
        _add_items(0, 2)
    two = queries()
    with quiet_build(main_user):
        _add_items(2, 6)
    six = queries()

    assert two == six
    assert six <= QUERY_CAPS[tab.name]


@pytest.fixture(name="tab_contents")
def fixture_tab_contents(client_logged):
    BorrowFactory(price=7000)
    LendFactory(price=9000)
    SavingFactory(saving_type=SavingTypeFactory(title="Fund A"))
    PensionFactory()
    ExpenseFactory(date=date(1999, 1, 1), price=100)
    IncomeFactory(price=600)
    # the next year's money differs, so a figure read for the wrong year shows
    IncomeFactory(date=date(2000, 1, 1), price=5000)

    return {tab.name: tab_fragment(client_logged, tab.url) for tab in INDEX_TABS}


CARD = (
    r'<div class="trend-card__label">{label}</div>\s*'
    r'<div class="trend-card__value[^>]*><span class="trend-card__figure"[^>]*>'
    r"{figure}<"
)
EMPTY_CARD = (
    r'<div class="trend-card__label">{label}</div>\s*'
    r'<div class="trend-card__value trend-card__value--empty">'
)
FIGURES = {
    "accounts": r"<span[^>]*>Account1</span>",
    "accounts_total": re.escape(ACCOUNTS_TOTAL.format(state="")),
    # start, end and balance of the year: 6,00 - 1,00 - 1,50 + 70,00 - 90,00
    "year_strip": (
        rf"<tr>\s*<td{FIGURE}>-</td>\s*<td{FIGURE}>-16,50</td>\s*"
        rf'<td{FIGURE} data-sign="loss">-16,50</td>'
    ),
    "no_incomes": rf'<td class="text-left">Pinigai, €</td>\s*<td{FIGURE}>-16,50</td>',
    "money": CARD.format(label="Pinigai", figure="-17"),
    "wealth": CARD.format(label="Turtas", figure="-17"),
    # 6,00 in and 1,00 out over the twelve months of a year that is over
    "average_incomes": CARD.format(label="Vidutinės pajamos", figure="1"),
    "average_expenses": CARD.format(label="Vidutinės išlaidos", figure="0"),
    # its rows: test_overview_debts_column_stays_and_draws_a_row_per_kind_with_a_debt
    "debts": r'<h2 class="panel__title">Skolos</h2>',
    # 1,50 of savings over 6,00 of incomes; neither fund has a worth, so no profit
    "saved_share": CARD.format(label="Pajamų dalis pervedama taupymui", figure="25,0"),
    "fund_profit": EMPTY_CARD.format(label="Fondų pelnas"),
    "pension_profit": EMPTY_CARD.format(label="Pensijų pelnas"),
    # nothing before the year, then the year's transfer
    "funds": (
        r"<td[^>]*>Fund A</td>\s*<td[^>]*>-</td>\s*<td[^>]*>-</td>\s*"
        rf'<td{GROUP_FIGURE} data-cell="">1,50</td>'
    ),
    "pensions": (
        r"<td[^>]*>PensionType</td>\s*<td[^>]*>-</td>\s*<td[^>]*>-</td>\s*"
        rf'<td{GROUP_FIGURE} data-cell="">1,00</td>'
    ),
    "year_heads": r"<th>1999</th>",
    # January's balance, after its incomes and expenses; the total row holds it too
    "month_balance": (
        rf"<td>Sausis</td>(?:\s*<td[^>]*>[^<]*</td>){{2}}\s*"
        rf'<td{FIGURE} data-sign="gain" data-cell="">5,00</td>'
    ),
    "year_end": rf'<td{FIGURE} data-sign="\w+" data-cell="" data-check="">',
    # January's expense in its type's column; the month balance's January reads 6,00
    "expenses_by_type": rf'<td>Sausis</td>\s*<td{FIGURE} data-cell="">1,00</td>',
}


def _lend():
    LendReturnFactory(debt=LendFactory(price=9000), price=3000)


def _borrow():
    BorrowReturnFactory(debt=BorrowFactory(price=7000), price=2000)


DEBTS_HEAD = ("", "Suma", "Grąžinta", "Liko")
GRID_COLUMN = '<div class="overview-grid__column">'
LENT = ("Paskolinta", "90,00", "30,00", "60,00")
BORROWED = ("Pasiskolinta", "70,00", "20,00", "50,00")
PANELS = re.compile(PANEL_TITLE + r"(.*?)</section>", re.S)


def _panels(content, title):
    """What each Panel titled `title` holds."""
    return [body for drawn, body in PANELS.findall(content) if drawn == title]


def _debts_tables(content):
    """Each Skolos Panel's header row, then its rows, (title, Suma, Grąžinta, Liko)."""
    return [
        [
            tuple(c.strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row))
            for row in re.findall(r"<tr>(.*?)</tr>", panel, re.S)
        ]
        for panel in _panels(content, "Skolos")
    ]


@pytest.mark.parametrize(
    "debts, tables",
    [
        pytest.param([_borrow, _lend], [[DEBTS_HEAD, LENT, BORROWED]], id="both"),
        pytest.param([_lend], [[DEBTS_HEAD, LENT]], id="lend-only"),
        pytest.param([], [], id="none"),
    ],
)
def test_overview_debts_column_stays_and_draws_a_row_per_kind_with_a_debt(
    client_logged, debts, tables
):
    for debt in debts:
        debt()

    content = tab_fragment(client_logged, INDEX_TABS["overview"].url)

    # with no open debt the grid keeps its third column
    assert (_debts_tables(content), content.count(GRID_COLUMN)) == (tables, 3)


def test_overview_draws_the_year_strip_in_its_panel_and_the_forecast_folded(
    client_logged,
):
    content = tab_fragment(client_logged, INDEX_TABS["overview"].url)
    year_strip = [
        (re.findall(BOXED_TABLE, body), cell_texts(body))
        for body in _panels(content, "1999 metai")
    ]

    # the year's three figures, under its titles; the forecast waits for its click
    forecast = [body.strip() for body in _panels(content, "Prognozė")]

    assert (year_strip, forecast) == (
        [
            (
                ["main striped hover"],
                [["1999 pradžioje", "1999 pabaigoje", "Balansas"], ["-", "-", "-"]],
            )
        ],
        ['<div id="forecast" x-show="open"></div>'],
    )


LEGACY_CLASSES = (
    "left-thick-border",
    "right-thick-border",
    "long-price-col",
    "no-right-border",
    "text-nowrap",
    "no-hover",
    "year-expenses",
    "no-categories",
    "right-thin-border",
    "left-thin-border",
    "title-col",
    "funds-title-col-min-width",
)


@pytest.mark.parametrize(
    "tab, titles, tables, totals, bare_cells",
    [
        pytest.param(
            "overview",
            ["Sąskaitos", "1999 metai", "Prognozė", "Be pajamų", "Skolos"],
            4,
            1,
            [],
            id="overview",
        ),
        # Fund A and the pension: no worth, so no check date
        pytest.param(
            "funds",
            ["Fondai", "Pensijos"],
            2,
            2,
            [' class="main__date main__group-start" data-cell="empty"'] * 2,
            id="funds",
        ),
        # each table's average and total rows; the average row's End of year label
        pytest.param(
            "balance", ["Balansas", "Išlaidų statistika"], 2, 4, [""], id="balance"
        ),
    ],
)
def test_index_tables_wear_the_skin_and_no_legacy_class(
    tab_contents, tab, titles, tables, totals, bare_cells
):
    content = tab_contents[tab]

    drawn = re.findall(PANEL_TITLE, content)
    boxed = re.findall(BOXED_TABLE, content)
    total_rows = re.findall(r'<tr class="(main__total)">', content)
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", content, re.S)
    # a row's first cell is its name, unless it holds a figure (the Year strip's)
    bare = [
        cell
        for row in rows
        for at, (cell, text) in enumerate(re.findall(r"<td([^>]*)>([^<]*)", row))
        if "main__figure" not in cell and (at or re.fullmatch(r"[-\d.,]+", text))
    ]
    legacy = re.findall(rf'class="[^"]*\b({"|".join(LEGACY_CLASSES)})\b', content)

    assert (drawn, boxed, total_rows, bare, legacy) == (
        titles,
        ["main striped hover"] * tables,
        ["main__total"] * totals,
        bare_cells,
        [],
    )


def test_expenses_by_type_head_cuts_a_long_type_and_tips_it_whole(client_logged):
    ExpenseFactory(expense_type=ExpenseTypeFactory(title="Laisvalaikis"))

    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    head = [
        cell
        for panel in _panels(content, "Išlaidų statistika")
        for cell in re.findall(
            r'<th><span class="tip bottom" tabindex="0" data-tip="([^"]*)"'
            r' aria-description="\1">([^<]*)</span></th>',
            panel.partition("</thead>")[0],
        )
    ]

    # cut to eight with its ellipsis; the tooltip reads it in full (Q57); the
    # factory's expense name brings its own type
    assert head == [("Expense Type", "Expense…"), ("Laisvalaikis", "Laisval…")]


@pytest.mark.parametrize(
    "today, averages",
    [
        pytest.param("2000-06-01", ["16,67", "166,67", "183,33"], id="past-of-twelve"),
        # March is not reached: its 900,00 is in no average
        pytest.param("1999-02-15", ["100,00", "550,00", "650,00"], id="running-of-two"),
    ],
)
def test_expenses_by_type_table_draws_each_cell(client_logged, today, averages):
    food, rent = (ExpenseTypeFactory(title=title) for title in ("Food", "Rent"))
    ExpenseFactory(expense_type=food, price=20000, date=date(1999, 1, 1))
    ExpenseFactory(expense_type=rent, price=40000, date=date(1999, 1, 1))
    ExpenseFactory(expense_type=rent, price=70000, date=date(1999, 2, 1))
    ExpenseFactory(expense_type=rent, price=90000, date=date(1999, 3, 1))

    with time_machine.travel(today, tick=False):
        content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    (panel,) = _panels(content, "Išlaidų statistika")
    rows = [
        (
            re.findall(r"<td>([^<]*)</td>", row),
            re.findall(
                r'<td class="main__figure" data-cell="([^"]*)">([^<]*)</td>', row
            ),
        )
        for row in re.findall(
            r"<tr\b[^>]*>(.*?)</tr>", panel.partition("</thead>")[2], re.S
        )
    ]

    # each figure cell with its state; the factory's expense name brings its own
    # type, with no expense; each average divides by the months the year has reached
    none = ("empty", "-")
    assert [*rows[:2], *rows[-2:]] == [
        (["Sausis"], [none, ("", "200,00"), ("", "400,00"), ("", "600,00")]),
        (["Vasaris"], [none, none, ("", "700,00"), ("", "700,00")]),
        (["Vidurkis"], [none, *[("", average) for average in averages]]),
        (["Viso"], [none, ("", "200,00"), ("", "2.000,00"), ("", "2.200,00")]),
    ]


def _accounts_and_debts(content):
    return (table_titled(content, "Sąskaitos"), *_panels(content, "Skolos"))


@pytest.mark.parametrize(
    "tab, tables, count",
    [
        # Account1's five, the total's five, three for each kind of debt
        pytest.param("overview", _accounts_and_debts, 16, id="overview"),
        # twelve months of ten figures but January's signed balance, eight in each
        # foot row; twelve months, the average and the total of one type and its sum
        pytest.param("balance", lambda content: [content], 119 + 16 + 28, id="balance"),
    ],
)
def test_index_tables_unsigned_money_cells_carry_their_cell_state(
    tab_contents, tab, tables, count
):
    cells = [
        (attrs, text)
        for table in tables(tab_contents[tab])
        for attrs, text in re.findall(
            r'<td class="main__figure"([^>]*)>([-\d.,]+)</td>', table
        )
        if "data-sign" not in attrs
    ]
    states = {
        (text == "-", tuple(re.findall(r'data-cell="(\w*)"', attrs)))
        for attrs, text in cells
    }

    # a zero is "empty", every other figure ""
    assert (len(cells), states) == (count, {(True, ("empty",)), (False, ("",))})


def test_each_index_figure_is_drawn_on_exactly_one_tab(tab_contents):
    found = {
        name: {
            tab: count
            for tab, content in tab_contents.items()
            if (count := len(re.findall(figure, content)))
        }
        for name, figure in FIGURES.items()
    }

    assert found == {
        "accounts": {"overview": 1},
        "accounts_total": {"overview": 1},
        "year_strip": {"overview": 1},
        "no_incomes": {"overview": 1},
        "money": {"overview": 1},
        "wealth": {"overview": 1},
        "average_incomes": {"overview": 1},
        "average_expenses": {"overview": 1},
        "debts": {"overview": 1},
        "saved_share": {"funds": 1},
        "fund_profit": {"funds": 1},
        "pension_profit": {"funds": 1},
        "funds": {"funds": 1},
        "pensions": {"funds": 1},
        "year_heads": {"balance": 2},
        "month_balance": {"balance": 1},
        "year_end": {"balance": 1},
        "expenses_by_type": {"balance": 1},
    }


@pytest.mark.parametrize("tab", INDEX_TABS, ids=lambda tab: tab.name)
def test_no_index_tab_draws_a_fetching_button(client_logged, tab):
    content = tab_fragment(client_logged, tab.url)

    assert re.findall(r"<button\b[^>]*\bhx-get=[^>]*>", content) == []


def test_quick_add_offers_each_worth_pill_on_its_own_tab(client_logged):
    content = client_logged.get(INDEX_TABS["overview"].url).content.decode()

    assert [
        (url, label, tab) for _tag, tab, url, label in quick_add_pills(content)
    ] == [
        (f'hx-get="{reverse(url_name)}"', label, tab)
        for url_name, label, tab in (
            ("bookkeeping:accounts_worth_new", "Sąskaitų faktas", "overview"),
            ("bookkeeping:savings_worth_new", "Fondų faktas", "funds"),
            ("bookkeeping:pensions_worth_new", "Pensijų faktas", "funds"),
        )
    ]


TAG = re.compile(r"<\w+\b[^>]*>")


@pytest.mark.parametrize("tab", INDEX_TABS, ids=lambda tab: tab.name)
def test_an_index_tab_reloads_whole_on_reload_alone(client_logged, tab):
    content = tab_fragment(client_logged, tab.url)

    tags = (
        dict(re.findall(r"""([\w-]+)=["']([^"']*)["']""", tag))
        for tag in TAG.findall(content)
    )
    listeners = [
        (tag.get("hx-get", ""), tag["hx-trigger"])
        for tag in tags
        if "from:body" in tag.get("hx-trigger", "")
    ]

    assert listeners == [(tab.url, "reload from:body")]


def test_only_the_charts_tab_draws_each_chart_and_its_data(tab_contents):
    # the id stays on the chart's own box, where its redraw looks it up
    charts = {
        tab: found
        for tab, content in tab_contents.items()
        if (
            found := re.findall(PANEL_TITLE + r'<div id="([^"]*)"></div>', content)
            + re.findall(r'<script id="([\w-]+-data)"', content)
        )
    }

    assert charts == {
        "charts": [
            ("Išlaidos pagal rūšis", "chart-expenses-container"),
            ("Balansas per mėnesį", "chart-balance-container"),
            ("Pajamos ir išlaidos", "chart-incomes-expenses-container"),
            "chart-expenses-data",
            "month-charts-data",
        ]
    }


@time_machine.travel("1999-02-15")
def test_view_index_renders_its_chart_data(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    content = tab_fragment(client_logged, INDEX_TABS["charts"].url)
    month_charts = script_json(content, "month-charts-data")
    expenses = script_json(content, "chart-expenses-data")

    # today's month is the selected year's current month, the next one not reached
    assert (month_charts["expenses"][:3], month_charts["current_month"][:3]) == (
        [100, 0, None],
        [False, True, False],
    )
    assert [point["y"] for point in expenses] == [100]


@pytest.mark.parametrize(
    ("view_class", "read", "average"),
    [
        (TabOverview, lambda context: context["cards"][3].value, "150"),
        (TabOverview, lambda context: context["avg_expenses"], 10000),
        (TabCharts, lambda context: context["month_charts"]["expenses_average"], 15000),
    ],
    ids=["card-of-4-months", "no-incomes-of-the-last-6", "chart-of-4-months"],
)
def test_an_index_tab_averages_over_the_months_its_views_today_reached(
    rf, main_user, view_class, read, average
):
    ExpenseFactory(price=60000, date=date(1999, 1, 6))
    view = view_for(rf, main_user, view_class)
    # apart from the clock, so a read of the clock shows
    view.today = date(1999, 4, 10)

    assert read(view.get_context_data()) == average


def test_balance_tables_name_their_columns_and_foot_rows(client_logged):
    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)

    labels = [
        (
            [
                re.sub(r"<[^>]+>", "", cell).strip()
                for cell in re.findall(
                    r"<th\b[^>]*>(.*?)</th>", table.partition("</thead>")[0], re.S
                )
            ],
            re.findall(r"<td[^>]*>([^<\d,.-]+)</td>", table.partition("<tfoot>")[2]),
        )
        for table in re.findall(r"<table\b.*?</table>", content, re.S)
    ]

    # the toggle's words are Alpine's, read by the webtest; no expense type, no column
    assert labels == [
        (
            ["", "Taupymas", "Skolos", ""]
            + ["1999", "Pajamos", "Išlaidos", "Balansas", "Investuota", "Parduota"]
            + ["Pasiskolinta", "Grąžinau", "Paskolinta", "Grąžino", "Pinigų srautas"],
            ["Vidurkis", "Metų pabaigoje", "Viso"],
        ),
        (["1999", "Viso"], ["Vidurkis", "Viso"]),
    ]


def _accounts_hold_less():
    AccountBalance.objects.filter(year=1999).update(balance=99900)


@pytest.mark.parametrize(
    "fee_source, skews, equal, state",
    [
        *(
            pytest.param(source, [], True, "", id=source)
            for source in SavingType.FeeSource.values
        ),
        pytest.param(
            SavingType.FeeSource.values[0],
            [_accounts_hold_less],
            False,
            "mismatch",
            id="mismatch",
        ),
    ],
)
def test_view_index_year_end_cash_flow_equals_the_accounts_balance(
    client_logged, fee_source, skews, equal, state
):
    IncomeFactory(price=100000)
    # the next year's accounts hold more, so a check reading them is never equal
    IncomeFactory(date=date(2000, 1, 1), price=5000)
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )
    for skew in skews:
        skew()

    balance = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    overview = tab_fragment(client_logged, INDEX_TABS["overview"].url)
    year_end = total_cells(balance[balance.index('id="table-balance"') :])[-1]
    accounts_balance = total_cells(table_titled(overview, "Sąskaitos"))[4]

    # each foot cell as the tab's reload draws it
    assert (
        year_end == accounts_balance != "",
        re.findall(CASH_FLOW_CELL, balance + overview),
    ) == (
        equal,
        [YEAR_END.format(state=state), ACCOUNTS_TOTAL.format(state=state)],
    )


def _signed_year():
    fund = SavingTypeFactory(title="Up")
    buy(fund, 100000)
    worth(fund, 150000)
    # Even holds what it should; the year's balance is -20,00
    even = AccountFactory(title="Even")
    IncomeFactory(account=even, price=1000)
    AccountWorthFactory(account=even, price=1000)
    ExpenseFactory(price=3000)


FOOT_END = r"\s*</tr>\s*</tfoot>"
GAIN_PROFIT = ' data-sign="gain" data-cell=""'


@pytest.mark.parametrize(
    "url, builds, cells, attrs",
    [
        # an empty year: every figure a zero
        *(
            pytest.param(
                lambda tab=tab: INDEX_TABS[tab].url,
                [],
                r"<td[^>]*data-sign",
                [],
                id=f"zero-{tab}",
            )
            for tab in ("overview", "balance")
        ),
        pytest.param(
            lambda: INDEX_TABS["funds"].url,
            [_signed_year],
            rf"<td([^>]*)>[^<]*</td>\s*<td([^>]*)>[^<]*</td>{FOOT_END}",
            [(f"{GROUP_FIGURE}{GAIN_PROFIT}", f"{FIGURE}{GAIN_PROFIT}")],
            id="profit-totals",
        ),
        pytest.param(
            lambda: INDEX_TABS["balance"].url,
            [_signed_year],
            # the total row's, not the month's balance of the same figure
            r"(?s)<td>Viso</td>.*?<td([^>]*)>-20,00</td>",
            [f'{FIGURE} data-sign="loss" data-cell=""'],
            id="year-total",
        ),
        # only the highlighted balance is signed, not the start or the end
        pytest.param(
            lambda: reverse("bookkeeping:forecast"),
            [_signed_year],
            r"<td([^>]*)>",
            [FIGURE, FIGURE, f'{FIGURE} data-sign="loss"'],
            id="forecast",
        ),
    ],
)
def test_view_a_signed_figure_carries_its_sign_and_a_zero_carries_none(
    client_logged, url, builds, cells, attrs
):
    for build in builds:
        build()

    content = tab_fragment(client_logged, url())

    assert re.findall(cells, content) == attrs


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_savings_column_shows_the_invested_price(client_logged, fee_source):
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    january = row_cells(content[content.index('id="table-balance"') :], "Sausis")

    assert january[3] == "200,00"


def test_balance_table_draws_each_column(client_logged):
    IncomeFactory(price=100000)
    ExpenseFactory(price=20000)
    SavingFactory(price=30000, fee=0)
    SavingCloseFactory(price=5000, fee=0)
    _borrow()
    _lend()

    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    table = content[content.index('id="table-balance"') :].partition("</table>")[0]
    rows = cell_texts(table)

    # in, out; saved, sold; borrowed, paid back; lent, paid back
    moves = [
        "1.000,00",
        "200,00",
        "300,00",
        "50,00",
        "70,00",
        "20,00",
        "90,00",
        "30,00",
    ]
    figures = [*moves[:2], "800,00", *moves[2:]]
    # each move over the twelve months of a year that is over
    averages = ["83,33", "16,67", "", "25,00", "4,17", "5,83", "1,67", "7,50", "2,50"]
    # January, then the average and total rows
    assert [rows[2], rows[-2], rows[-1]] == [
        ["Sausis", *figures, "540,00"],
        ["Vidurkis", *averages, "Metų pabaigoje"],
        ["Viso", *figures, "540,00"],
    ]


def test_balance_table_hides_its_debt_columns_until_asked(client_logged):
    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    table = content[content.index('id="table-balance"') :].partition("</table>")[0]
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, re.S)

    assert re.search(r'<table\b[^>]*x-data="\{ open:false \}"', table)
    # the debts group's head, then its four columns in every row
    assert [len(re.findall(r'<t[hd]\b[^>]*x-show="open"', row)) for row in rows] == [
        1,
        *[4] * 15,
    ]


def test_balance_tables_end_of_year_label_is_a_label_cell(client_logged):
    content = tab_fragment(client_logged, INDEX_TABS["balance"].url)
    table = content[content.index('id="table-balance"') :].partition("</table>")[0]

    # like Vidurkis beside it: a row name's face, not a figure's
    assert re.findall(r"<td\b[^>]*>\s*Metų pabaigoje", table) == ["<td>Metų pabaigoje"]
