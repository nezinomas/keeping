import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import count_queries
from ....debts.tests.factories import BorrowFactory, LendFactory
from ....expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ..helper import quiet_build, row_cells, script_json, total_cells

pytestmark = pytest.mark.django_db

INDEX_QUERY_CAP = 44
CASH_FLOW_CELL = r'<th[^>]*data-check="[^"]*">'
YEAR_END = '<th data-sign="gain" data-check="{state}">'
ACCOUNTS_TOTAL = '<th data-cell="" data-check="{state}">'


def _add_items(first, last):
    for i in range(first, last):
        IncomeFactory(income_type=IncomeTypeFactory(title=f"Type {i}"))
        ExpenseFactory(expense_type=ExpenseTypeFactory(title=f"Type {i}"))
        SavingFactory(saving_type=SavingTypeFactory(title=f"Type {i}"))
        PensionFactory(pension_type=PensionTypeFactory(title=f"Type {i}"))
        AccountFactory(title=f"Account {i}")
        BorrowFactory(name=f"Name {i}")
        LendFactory(name=f"Name {i}")


def test_view_index_queries_stay_under_the_cap_and_do_not_grow(
    client_logged, main_user
):
    url = reverse("bookkeeping:index")

    def queries():
        return count_queries(lambda: client_logged.get(url))

    with quiet_build(main_user):
        _add_items(0, 2)
    two = queries()
    with quiet_build(main_user):
        _add_items(2, 4)
    four = queries()

    assert two == four
    assert four <= INDEX_QUERY_CAP


@pytest.fixture(name="index_content")
def fixture_index_content(client_logged):
    BorrowFactory(price=7000)
    LendFactory(price=9000)
    PensionFactory()
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    return client_logged.get(reverse("bookkeeping:index")).content.decode()


INDEX_MARKERS = {
    "year": "<th>1999</th>",
    "balance": '<td data-sign="loss" data-cell="">-1,00</td>',
    "balance_short": r'<th class="text-nowrap long-price-col">\s*1999 pabaigoje\s*</th>',
    "expenses": '<td class="left-thick-border" data-cell="">1,00</td>',
    "averages": r"<th>\s*Vidutinės pajamos\s*</th>",
    "borrow": r'<span class="tip bottom w100" data-tip="Liko grąžinti:  70,00">\s*70,00\s*</span>',
    "lend": r'<span class="tip bottom w100" data-tip="Liko grąžinti:  90,00">\s*90,00\s*</span>',
    "accounts": ">Account1</span>",
    "savings": r'id="savings"[^>]*>\s*<div class="alert [^"]*">Pajamų dalis pervedama taupymui',
    "pensions": ">PensionType</td>",
    "wealth": r"<th>\s*Turtas\s*</th>",
    "no_incomes": r'<th class="long-price-col">€ \+ F \+ P</th>',
}


def test_view_index_renders_its_tables_and_panels(index_content):
    missing = [
        name
        for name, marker in INDEX_MARKERS.items()
        if not re.search(marker, index_content)
    ]

    assert missing == []


@pytest.mark.parametrize("url_name", ["bookkeeping:index", "bookkeeping:reload_index"])
def test_view_index_renders_its_chart_data(client_logged, url_name):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    content = client_logged.get(reverse(url_name)).content.decode()
    balance = script_json(content, "chart-balance-data")
    expenses = script_json(content, "chart-expenses-data")

    assert balance["expenses"][0] == 100
    assert [point["y"] for point in expenses] == [100]


def test_view_index_foot_rows_name_the_average(index_content):
    labels = re.findall(r"<tfoot>\s*<tr>\s*<th>([^<]*)</th>", index_content)

    assert labels == ["Vidurkis", "Vidurkis"]


def test_view_index_names_each_chart_data_element_once(index_content):
    ids = [
        "chart-balance-data",
        "chart-expenses-data",
        "chart-balance-source",
        "chart-expenses-source",
    ]

    counts = [index_content.count(f'id="{element_id}"') for element_id in ids]

    assert counts == [1, 1, 1, 1]


def test_view_index_accounts_reload_on_a_saved_move(index_content):
    listeners = re.findall(
        r'<div id="accounts" hx-get="([^"]*)" hx-trigger="([^"]*)"', index_content
    )

    assert listeners == [
        (
            reverse("bookkeeping:accounts"),
            "afterAccountWorthNew from:body, afterReset from:body, "
            "afterSignalAccounts from:body, afterSignal from:body, reload from:body",
        )
    ]


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_year_end_cash_flow_equals_the_accounts_balance(
    client_logged, fee_source
):
    IncomeFactory(price=100000)
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()
    year_end = total_cells(content[content.index('id="table-balance"') :])[-1]
    accounts_balance = total_cells(content[content.index('id="accounts"') :])[4]

    assert year_end == accounts_balance != ""
    assert re.findall(CASH_FLOW_CELL, content) == [
        YEAR_END.format(state=""),
        ACCOUNTS_TOTAL.format(state=""),
    ]


@pytest.mark.parametrize(
    "url_name, cells",
    [
        pytest.param("bookkeeping:index", [YEAR_END, ACCOUNTS_TOTAL], id="index"),
        pytest.param("bookkeeping:reload_index", [YEAR_END], id="reload"),
        pytest.param("bookkeeping:accounts", [ACCOUNTS_TOTAL], id="accounts"),
    ],
)
@pytest.mark.parametrize(
    "accounts_balance, state",
    [
        pytest.param(100000, "", id="equal"),
        pytest.param(99900, "mismatch", id="differ"),
    ],
)
def test_view_cash_flow_check_marks_each_foot_cell(
    client_logged, url_name, cells, accounts_balance, state
):
    IncomeFactory(price=100000)
    AccountBalance.objects.update(balance=accounts_balance)

    content = client_logged.get(reverse(url_name)).content.decode()

    assert re.findall(CASH_FLOW_CELL, content) == [
        cell.format(state=state) for cell in cells
    ]


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_savings_column_shows_the_invested_price(client_logged, fee_source):
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()
    january = row_cells(content[content.index('id="table-balance"') :], "Sausis")

    assert january[3] == "200,00"


def test_view_index_regenerate_buttons(client_logged):
    SavingFactory()
    PensionFactory()

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()
    url = re.escape(reverse("bookkeeping:regenerate_balances"))

    tips = re.findall(
        rf'<button[^>]*hx-get="{url}"[^>]*><span[^>]*data-tip="([^"]*)"', content
    )

    assert tips == ["Bus atnaujinti visų metų balansai."]


def test_view_reload_renders_the_index(client_logged):
    shown = {
        'hx-swap-oob="innerHTML:#table-balance"': 1,
        'hx-swap-oob="innerHTML:#table-expenses"': 1,
        'hx-swap-oob="innerHTML:#chart-balance-source"': 1,
        'hx-swap-oob="innerHTML:#chart-expenses-source"': 1,
        "<th>1999</th>": 2,
    }
    url = reverse("bookkeeping:reload_index")
    content = client_logged.get(url).content.decode("utf-8")

    assert {text: content.count(text) for text in shown} == shown


def test_view_reload_anonymous(client):
    url = reverse("bookkeeping:reload_index")
    response = client.get(url)

    assert response.url == f"{reverse('users:login')}?next={url}"
