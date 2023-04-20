import pytest
from django.urls import resolve, reverse

from ...pensions.factories import PensionFactory
from ...savings.factories import SavingFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_view_index_func():
    view = resolve("/")

    assert views.Index == view.func.view_class


def test_view_index_200(client_logged):
    response = client_logged.get("/")

    assert response.status_code == 200


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


def test_view_index_regenerate_buttons(client_logged):
    SavingFactory()
    PensionFactory()

    url = reverse("bookkeeping:index")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{ url }"' in content
    assert "Bus atnaujinti visų metų balansai." in content
