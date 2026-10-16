import pytest
from django.urls import reverse

from ....pensions.tests.factories import PensionFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ..factories import PensionWorthFactory, SavingWorthFactory
from ..helper import script_json

pytestmark = pytest.mark.django_db

CHART_TITLES = {
    "funds": "Fondai",
    "shares": "Akcijos",
    "pensions": "Pensijos III",
    "pensions2": "Pensijos II",
    "funds_shares": "Fondai, Akcijos",
    "funds_shares_pensions": "Fondai, Akcijos, Pensijos III",
}


def test_view_summary_savings_renders_its_charts(client_logged):
    PensionWorthFactory(pension_type=PensionFactory().pension_type)
    for title, kind in (("x", "shares"), ("y", "funds"), ("z", "pensions")):
        fund = SavingTypeFactory(title=title, type=kind)
        SavingFactory(saving_type=fund)
        SavingWorthFactory(saving_type=fund)

    url = reverse("bookkeeping:summary_savings")
    content = client_logged.get(url).content.decode("utf-8")

    for pointer, title in CHART_TITLES.items():
        assert f'<div id="{pointer}"></div>' in content
        chart = script_json(content, f"{pointer}_data")
        assert chart["title"] == title
        assert chart["categories"]


def test_view_summary_savings_no_records(client_logged):
    url = reverse("bookkeeping:summary_savings")
    content = client_logged.get(url).content.decode("utf-8")

    assert '<div class="alert alert-warning">' in content
    for pointer in CHART_TITLES:
        assert f'<div id="{pointer}"></div>' not in content
        assert f'<script id="{pointer}_data"' not in content
