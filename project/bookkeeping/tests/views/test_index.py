import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import count_queries, paper_page_parts, tab_fragment
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
from ...tabs import INDEX_TABS
from ..factories import AccountWorthFactory
from ..helper import quiet_build, row_cells, script_json, table_titled, total_cells
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db

CASH_FLOW_CELL = r'<t[hd][^>]*data-check="[^"]*">'
YEAR_END = '<th data-sign="gain" data-check="{state}">'
ACCOUNTS_TOTAL = '<td class="main__figure" data-cell="" data-check="{state}">'
FIGURE = ' class="main__figure"'


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
        "quick-add": False,
        "sticky headers": False,
        "tab panel": whole,
    }


@pytest.mark.parametrize("tab", INDEX_TABS, ids=lambda tab: tab.name)
def test_an_index_tab_sends_the_anonymous_to_the_login(client, tab):
    response = client.get(tab.url)

    assert response.url == f"{reverse('users:login')}?next={tab.url}"


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
FIGURES = {
    "accounts": r"<span[^>]*>Account1</span>",
    "accounts_total": re.escape(ACCOUNTS_TOTAL.format(state="")),
    # start, end and balance of the year: 6,00 - 1,00 - 1,50 + 70,00 - 90,00
    "year_strip": (
        rf"<td></td>\s*<td{FIGURE}>-</td>\s*<td{FIGURE}>-16,50</td>\s*"
        rf'<td{FIGURE} data-sign="loss">-16,50</td>'
    ),
    "no_incomes": rf'<td class="text-left">Pinigai, €</td>\s*<td{FIGURE}>-16,50</td>',
    "money": CARD.format(label="Pinigai", figure="-17"),
    "wealth": CARD.format(label="Turtas", figure="-17"),
    "average_incomes": CARD.format(label="Vidutinės pajamos", figure="6"),
    "average_expenses": CARD.format(label="Vidutinės išlaidos", figure="1"),
    "borrow": rf'<td class="text-left">Pasiskolinta</td>\s*<td{FIGURE}[^>]*>70,00<',
    "lend": rf'<td class="text-left">Paskolinta</td>\s*<td{FIGURE}[^>]*>90,00<',
    "saved_share": r"<div[^>]*>Pajamų dalis pervedama taupymui: <b>25,0</b>%",
    # nothing before the year, then the year's transfer
    "funds": (
        r"<td[^>]*>Fund A</td>\s*<td[^>]*>-</td>\s*<td[^>]*>-</td>\s*"
        r'<td data-cell="">1,50</td>'
    ),
    "pensions": (
        r"<td[^>]*>PensionType</td>\s*<td[^>]*>-</td>\s*<td[^>]*>-</td>\s*"
        r'<td data-cell="">1,00</td>'
    ),
    "year_heads": r"<th>1999</th>",
    "month_balance": r'<td data-sign="gain" data-cell="">5,00</td>',
    "year_end": r'<th data-sign="\w+" data-check="">',
    # January's expense in its type's column; the month balance's January reads 6,00
    "expenses_by_type": r'<td>Sausis</td>\s*<td data-cell="">1,00</td>',
    "chart_balance": r'<script id="chart-balance-data"',
    "chart_expenses": r'<script id="chart-expenses-data"',
}


def _lend():
    LendReturnFactory(debt=LendFactory(price=9000), price=3000)


def _borrow():
    BorrowReturnFactory(debt=BorrowFactory(price=7000), price=2000)


LENT = ("Paskolinta", "90,00", "30,00", "60,00")
BORROWED = ("Pasiskolinta", "70,00", "20,00", "50,00")
DEBTS_PANEL = re.compile(r'<h2 class="panel__title">Skolos</h2>(.*?)</section>', re.S)


def _debts_tables(content):
    """The body rows of each Skolos Panel, (title, Suma, Grąžinta, Liko) each."""
    return [
        [
            tuple(cell.strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", row))
            for row in re.findall(r"<tr>(.*?)</tr>", panel.split("</thead>")[-1], re.S)
        ]
        for panel in DEBTS_PANEL.findall(content)
    ]


@pytest.mark.parametrize(
    "debts, tables",
    [
        pytest.param([_borrow, _lend], [[LENT, BORROWED]], id="both"),
        pytest.param([_lend], [[LENT]], id="lend-only"),
        pytest.param([], [], id="none"),
    ],
)
def test_overview_debts_table_draws_a_row_per_kind_with_a_debt(
    client_logged, debts, tables
):
    for debt in debts:
        debt()

    content = tab_fragment(client_logged, INDEX_TABS["overview"].url)

    assert _debts_tables(content) == tables


LEGACY_CLASSES = ("left-thick-border", "long-price-col", "no-right-border")


def test_overview_tables_wear_the_skin_and_no_legacy_class(tab_contents):
    content = tab_contents["overview"]

    titles = re.findall(r'<h2 class="panel__title">([^<]*)</h2>', content)
    boxed = re.findall(
        r'<div class="table-responsive">\s*<table class="([^"]*)"', content
    )
    totals = re.findall(r'<tr class="(main__total)">', content)
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", content, re.S)
    bare = [
        cell
        for row in rows
        for cell in re.findall(r"<td([^>]*)>", row)[1:]
        if "main__figure" not in cell
    ]
    legacy = [name for name in LEGACY_CLASSES if name in content]

    assert (titles, boxed, totals, bare, legacy) == (
        ["Sąskaitos", "Be pajamų", "Skolos"],
        ["main striped hover"] * 4,
        ["main__total"],
        [],
        [],
    )


def test_overview_unsigned_money_cells_carry_their_cell_state(tab_contents):
    content = tab_contents["overview"]
    tables = (table_titled(content, "Sąskaitos"), *DEBTS_PANEL.findall(content))

    cells = [
        (attrs, text)
        for table in tables
        for attrs, text in re.findall(
            r'<td class="main__figure"([^>]*)>([^<]*)</td>', table
        )
        if "data-sign" not in attrs
    ]
    states = {
        (text == "-", tuple(re.findall(r'data-cell="(\w*)"', attrs)))
        for attrs, text in cells
    }

    # Account1's five, the total's five, three for each kind of debt: a zero
    # (the account's start) is "empty", every other figure ""
    assert (len(cells), states) == (16, {(True, ("empty",)), (False, ("",))})


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
        "borrow": {"overview": 1},
        "lend": {"overview": 1},
        "saved_share": {"funds": 1},
        "funds": {"funds": 1},
        "pensions": {"funds": 1},
        "year_heads": {"balance": 2},
        "month_balance": {"balance": 1},
        "year_end": {"balance": 1},
        "expenses_by_type": {"balance": 1},
        "chart_balance": {"charts": 1},
        "chart_expenses": {"charts": 1},
    }


BUTTON = re.compile(r'<button\b[^>]*\bhx-get="([^"]*)"[^>]*>(.*?)</button>', re.S)


def _buttons(content):
    """(url, label, tips) of each button that fetches."""
    return [
        (url, re.sub(r"<[^>]+>", "", inner), re.findall(r'data-tip="([^"]*)"', inner))
        for url, inner in BUTTON.findall(content)
    ]


@pytest.mark.parametrize(
    "tab, buttons",
    [
        pytest.param(
            "overview",
            [
                ("bookkeeping:accounts_worth_new", "Sąskaitų faktas", []),
                (
                    "bookkeeping:regenerate_balances",
                    "Atnaujinti balansus",
                    ["Bus atnaujinti visų metų balansai."],
                ),
            ],
            id="overview",
        ),
        pytest.param(
            "funds",
            [
                ("bookkeeping:savings_worth_new", "Fondų faktas", []),
                ("bookkeeping:pensions_worth_new", "Pensijų faktas", []),
            ],
            id="funds",
        ),
        pytest.param("balance", [], id="balance"),
        pytest.param("charts", [], id="charts"),
    ],
)
def test_each_index_tab_draws_the_buttons_of_its_worth(client_logged, tab, buttons):
    content = tab_fragment(client_logged, INDEX_TABS[tab].url)

    assert _buttons(content) == [
        (reverse(url_name), label, tips) for url_name, label, tips in buttons
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


def test_view_index_renders_its_chart_data(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    content = tab_fragment(client_logged, reverse("bookkeeping:tab_charts"))
    balance = script_json(content, "chart-balance-data")
    expenses = script_json(content, "chart-expenses-data")

    assert balance["expenses"][0] == 100
    assert [point["y"] for point in expenses] == [100]


def test_view_index_foot_rows_name_the_average(tab_contents):
    labels = re.findall(r"<tfoot>\s*<tr>\s*<th>([^<]*)</th>", tab_contents["balance"])

    assert labels == ["Vidurkis", "Vidurkis"]


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_year_end_cash_flow_equals_the_accounts_balance(
    client_logged, fee_source
):
    IncomeFactory(price=100000)
    # the next year's accounts hold more, so a check reading them is never equal
    IncomeFactory(date=date(2000, 1, 1), price=5000)
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    balance = tab_fragment(client_logged, reverse("bookkeeping:tab_balance"))
    overview = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))
    year_end = total_cells(balance[balance.index('id="table-balance"') :])[-1]
    accounts_balance = total_cells(table_titled(overview, "Sąskaitos"))[4]

    assert year_end == accounts_balance != ""
    assert re.findall(CASH_FLOW_CELL, balance + overview) == [
        YEAR_END.format(state=""),
        ACCOUNTS_TOTAL.format(state=""),
    ]


@pytest.mark.parametrize(
    "url_name, cells",
    [
        pytest.param("bookkeeping:tab_overview", [ACCOUNTS_TOTAL], id="overview"),
        pytest.param("bookkeeping:tab_balance", [YEAR_END], id="balance"),
    ],
)
# the two figures equal: test_view_index_year_end_cash_flow_equals_the_accounts_balance
def test_view_cash_flow_check_marks_each_foot_cell_of_a_mismatch(
    client_logged, url_name, cells
):
    IncomeFactory(price=100000)
    AccountBalance.objects.filter(year=1999).update(balance=99900)

    # what the tab's reload draws
    content = tab_fragment(client_logged, reverse(url_name))

    assert re.findall(CASH_FLOW_CELL, content) == [
        cell.format(state="mismatch") for cell in cells
    ]


@pytest.mark.parametrize(
    "url_name",
    [
        "bookkeeping:tab_overview",
        "bookkeeping:tab_balance",
    ],
)
def test_view_a_zero_figure_carries_no_sign(client_logged, url_name):
    content = tab_fragment(client_logged, reverse(url_name))

    assert "data-sign" not in content


FOOT_END = r"\s*</tr>\s*</tfoot>"
GAIN_PROFIT = ' data-sign="gain" data-cell=""'


@pytest.mark.parametrize(
    "url_name, cells, attrs",
    [
        pytest.param(
            "bookkeeping:tab_funds",
            rf"<th([^>]*)>[^<]*</th>\s*<th([^>]*)>[^<]*</th>{FOOT_END}",
            [(GAIN_PROFIT, GAIN_PROFIT)],
            id="profit-totals",
        ),
        pytest.param(
            "bookkeeping:tab_balance",
            r"<th([^>]*)>-20,00</th>",
            [' data-sign="loss"'],
            id="year-total",
        ),
        # only the highlighted balance is signed, not the start or the end
        pytest.param(
            "bookkeeping:forecast",
            r"<td([^>]*)>",
            ["", FIGURE, FIGURE, f'{FIGURE} data-sign="loss"'],
            id="forecast",
        ),
    ],
)
def test_view_a_signed_figure_carries_its_sign(client_logged, url_name, cells, attrs):
    fund = SavingTypeFactory(title="Up")
    buy(fund, 100000)
    worth(fund, 150000)
    # Even holds what it should; the year's balance is -20,00
    even = AccountFactory(title="Even")
    IncomeFactory(account=even, price=1000)
    AccountWorthFactory(account=even, price=1000)
    ExpenseFactory(price=3000)

    content = tab_fragment(client_logged, reverse(url_name))

    assert re.findall(cells, content) == attrs


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_savings_column_shows_the_invested_price(client_logged, fee_source):
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = tab_fragment(client_logged, reverse("bookkeeping:tab_balance"))
    january = row_cells(content[content.index('id="table-balance"') :], "Sausis")

    assert january[3] == "200,00"
