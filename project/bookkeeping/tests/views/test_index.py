import re
from datetime import date

import pytest
from django.urls import reverse

from ....debts.tests.factories import BorrowFactory, LendFactory
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ..helper import script_json

pytestmark = pytest.mark.django_db


def test_view_count_queries(client_logged, django_assert_max_num_queries):
    url = reverse("bookkeeping:index")
    with django_assert_max_num_queries(32):
        client_logged.get(url)


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


def test_view_index_negative_balance_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert re.search(r'<td data-sign="loss"[^>]*>-', content)


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

    url = reverse("bookkeeping:index")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("bookkeeping:regenerate_balances")

    assert f'hx-get="{url}"' in content
    assert "Bus atnaujinti visų metų balansai." in content


def test_view_reload_200(client_logged):
    url = reverse("bookkeeping:reload_index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_reload_anonymous(client):
    url = reverse("bookkeeping:reload_index")
    response = client.get(url)

    assert response.status_code == 302
