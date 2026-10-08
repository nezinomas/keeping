import pytest
from django.urls import reverse

from ....pensions.tests.factories import PensionFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ..factories import PensionWorthFactory, SavingWorthFactory

pytestmark = pytest.mark.django_db


def test_view_summery_savings_context(client_logged):
    PensionWorthFactory(pension_type=PensionFactory().pension_type)
    for title, kind in (("x", "shares"), ("y", "funds"), ("z", "pensions")):
        fund = SavingTypeFactory(title=title, type=kind)
        SavingFactory(saving_type=fund)
        SavingWorthFactory(saving_type=fund)

    url = reverse("bookkeeping:summary_savings")
    response = client_logged.get(url)

    assert "funds" in response.context["charts"]
    assert "shares" in response.context["charts"]
    assert "pensions2" in response.context["charts"]
    assert "pensions" in response.context["charts"]
    assert "funds_shares_pensions" in response.context["charts"]


def test_view_summery_savings_context_no_records(client_logged):
    url = reverse("bookkeeping:summary_savings")
    response = client_logged.get(url)

    assert "funds" not in response.context["charts"]
    assert "shares" not in response.context["charts"]
    assert "pensions2" not in response.context["charts"]
    assert "pensions" not in response.context["charts"]
    assert "funds_shares_pensions" not in response.context["charts"]

    assert response.context["records"] == 0
