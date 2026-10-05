import re
from datetime import date

import pytest
from django.urls import resolve, reverse

from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ... import views

pytestmark = pytest.mark.django_db


def test_view_index_func():
    view = resolve("/")

    assert views.Index == view.func.view_class


def test_view_index_200(client_logged):
    response = client_logged.get("/")

    assert response.status_code == 200


def test_view_count_queries(client_logged, django_assert_max_num_queries):
    url = reverse("bookkeeping:index")
    with django_assert_max_num_queries(32):
        client_logged.get(url)


def test_view_index_context(client_logged):
    url = reverse("bookkeeping:index")
    response = client_logged.get(url)

    assert "year" in response.context
    assert "balance" in response.context
    assert "balance_short" in response.context
    assert "expenses" in response.context
    assert "averages" in response.context
    assert "borrow" in response.context
    assert "lend" in response.context
    assert "chart_expenses" in response.context
    assert "chart_balance" in response.context
    assert "accounts" in response.context
    assert "savings" in response.context
    assert "pensions" in response.context
    assert "wealth" in response.context
    assert "no_incomes" in response.context


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
    checked = re.findall(r'class="[^"]*\bcheck">([^<]+)</th>', content)

    assert len(checked) == 2
    assert checked[0] == checked[1]


def test_view_index_negative_balance_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert re.search(r'<td data-sign="loss" class="[^"]*">-', content)


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_view_index_savings_column_shows_the_invested_price(client_logged, fee_source):
    SavingFactory(
        price=20000,
        fee=300,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    content = client_logged.get(reverse("bookkeeping:index")).content.decode()
    january = re.findall(r'<td class="left-thick-border[^"]*">([^<]+)</td>', content)

    assert january[0] == "200,00"


def test_view_index_regenerate_buttons(client_logged):
    SavingFactory()
    PensionFactory()

    url = reverse("bookkeeping:index")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{url}"' in content
    assert "Bus atnaujinti visų metų balansai." in content


def test_view_reload_func():
    view = resolve("/bookkeeping/reload_index/")

    assert views.ReloadIndex == view.func.view_class


def test_view_reload_200(client_logged):
    url = reverse("bookkeeping:reload_index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_reload_anonymous(client):
    url = reverse("bookkeeping:reload_index")
    response = client.get(url)

    assert response.status_code == 302
