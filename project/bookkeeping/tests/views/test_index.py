import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import count_queries
from ....debts.tests.factories import BorrowFactory, LendFactory
from ....expenses.tests.factories import ExpenseFactory, ExpenseTypeFactory
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ..helper import quiet_build, script_json

pytestmark = pytest.mark.django_db

INDEX_QUERY_CAP = 32


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
        _add_items(2, 6)
    six = queries()

    assert two == six
    assert six <= INDEX_QUERY_CAP


@pytest.fixture(name="index_content")
def fixture_index_content(client_logged):
    BorrowFactory(price=7000)
    LendFactory(price=9000)
    PensionFactory()
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    return client_logged.get(reverse("bookkeeping:index")).content.decode()


@pytest.mark.parametrize(
    "marker",
    [
        pytest.param("<th>1999</th>", id="year"),
        pytest.param('<td data-sign="loss" data-cell="">-1,00</td>', id="balance"),
        pytest.param("1999 pabaigoje", id="balance_short"),
        pytest.param(
            '<td class="left-thick-border" data-cell="">1,00</td>', id="expenses"
        ),
        pytest.param("Vidutinės pajamos", id="averages"),
        pytest.param('data-tip="Liko grąžinti:  70,00"', id="borrow"),
        pytest.param('data-tip="Liko grąžinti:  90,00"', id="lend"),
        pytest.param(">Account1</span>", id="accounts"),
        pytest.param("Pajamų dalis pervedama taupymui", id="savings"),
        pytest.param(">PensionType</td>", id="pensions"),
        pytest.param("Turtas", id="wealth"),
        pytest.param("€ + F + P", id="no_incomes"),
    ],
)
def test_view_index_renders_its_tables_and_panels(index_content, marker):
    assert marker in index_content


def test_view_index_renders_its_chart_data(index_content):
    balance = script_json(index_content, "chart-balance-data")
    expenses = script_json(index_content, "chart-expenses-data")

    assert balance["expenses"][0] == 100
    assert [point["y"] for point in expenses] == [100]


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
    checked = re.findall(
        r'<th[^>]*class="[^"]*\bcheck\b[^"]*"[^>]*>([^<]+)</th>', content
    )

    assert len(checked) == 2
    assert checked[0] == checked[1]


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_savings_column_shows_the_invested_price(client_logged, fee_source):
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()
    january = re.findall(
        r'<td class="left-thick-border[^"]*"[^>]*>([^<]+)</td>', content
    )

    assert january[0] == "200,00"


def test_view_index_regenerate_buttons(client_logged):
    SavingFactory()
    PensionFactory()

    response = client_logged.get(reverse("bookkeeping:index"))
    content = response.content.decode("utf-8")

    regenerate_url = reverse("bookkeeping:regenerate_balances")

    assert f'hx-get="{regenerate_url}"' in content
    assert "Bus atnaujinti visų metų balansai." in content


@pytest.mark.parametrize(
    "shown",
    [
        [
            'hx-swap-oob="innerHTML:#table-balance"',
            'hx-swap-oob="innerHTML:#table-expenses"',
            'hx-swap-oob="innerHTML:#chart-balance-data"',
            'hx-swap-oob="innerHTML:#chart-expenses-data"',
        ],
        ["<th>1999</th>"],
    ],
    ids=["index_blocks", "year_header"],
)
def test_view_reload_renders_the_index(client_logged, shown):
    url = reverse("bookkeeping:reload_index")
    content = client_logged.get(url).content.decode("utf-8")

    for text in shown:
        assert text in content


def test_view_reload_anonymous(client):
    url = reverse("bookkeeping:reload_index")
    response = client.get(url)

    assert response.status_code == 302
