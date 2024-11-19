import pytest
from django.urls import resolve, reverse

from ...pensions.factories import PensionFactory
from ...savings.factories import SavingFactory, SavingTypeFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_view_summary_savings_func():
    view = resolve("/summary/savings/")

    assert views.SummarySavings == view.func.view_class


def test_view_summary_savings_200(client_logged):
    url = reverse("bookkeeping:summary_savings")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_summery_savings_context(client_logged):
    PensionFactory()
    SavingFactory(saving_type=SavingTypeFactory(title="x", type="shares"))
    SavingFactory(saving_type=SavingTypeFactory(title="y", type="funds"))
    SavingFactory(saving_type=SavingTypeFactory(title="z", type="pensions"))

    url = reverse("bookkeeping:summary_savings")
    response = client_logged.get(url)

    assert "records" in response.context
    assert "funds" in response.context["charts"]
    assert "shares" in response.context["charts"]
    assert "pensions2" in response.context["charts"]
    assert "pensions" in response.context["charts"]
    assert "funds_shares_pensions" in response.context["charts"]


def test_view_summery_savings_context_no_records(client_logged):
    url = reverse("bookkeeping:summary_savings")
    response = client_logged.get(url)

    assert "records" in response.context
    assert "funds" not in response.context["charts"]
    assert "shares" not in response.context["charts"]
    assert "pensions2" not in response.context["charts"]
    assert "pensions" not in response.context["charts"]
    assert "funds_shares_pensions" not in response.context["charts"]

    assert response.context["records"] == 0
