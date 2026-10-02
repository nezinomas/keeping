from datetime import datetime

import pytest
import pytz
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse

from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ... import views
from ..factories import PensionWorthFactory
from ..helper import fund_with_a_sell, row_cells

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve("/bookkeeping/pensions/")

    assert views.Pensions == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context(client_logged):
    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    actual = response.context

    assert actual["title"] == "Pensijos"
    assert actual["type"] == "pensions"
    assert "object_list" in actual
    assert "total_row" in actual


def test_view_context_with_saving_type_pension(client_logged):
    PensionFactory()
    SavingFactory(saving_type=SavingTypeFactory(title="AAA", type="pensions"))

    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    actual = response.context["object_list"]

    assert len(actual) == 2
    assert actual[0].saving_type.title == "AAA"
    assert actual[1].pension_type.title == "PensionType"


def test_view_context_with_saving_type_pension_title_in_template(client_logged):
    PensionFactory()
    SavingFactory(saving_type=SavingTypeFactory(title="AAA", type="pensions"))

    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "AAA" in actual
    assert "PensionType" in actual


def test_view_latest_check(client_logged):
    PensionFactory()
    PensionWorthFactory()
    PensionWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    object_list = response.context["object_list"]

    assert object_list[0].latest_check == datetime(1999, 1, 1, 1, 3, 4, tzinfo=pytz.utc)


def test_table_percentage(client_logged):
    PensionFactory(price=660)

    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "6,60</td>" in actual  # row
    assert "6,60</th>" in actual  # total_row


def test_regenerate_buttons(client_logged):
    PensionFactory()

    url = reverse("bookkeeping:pensions")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{url}?type=pensions"' in content
    assert "Bus atnaujinti tik šios lentelės balansai." in content


def _pension_type_with_a_sell(title, closed=None):
    return fund_with_a_sell(
        title, 2596753, 3459722, fee=20000, kind="pensions", closed=closed
    )


def test_closed_pension_type_with_a_sell_shows_its_profit(client_logged):
    _pension_type_with_a_sell("INVL", closed=1999)

    content = client_logged.get(reverse("bookkeeping:pensions")).content.decode()
    cells = row_cells(content, "INVL")

    assert cells[8:10] == ["-", "-"]
    assert cells[10] == "8.429,69"
    assert cells[11] == "32,46%"


@pytest.mark.parametrize("sold", [True, False])
def test_open_pension_type_with_no_worth_shows_dashes(client_logged, sold):
    if sold:
        _pension_type_with_a_sell("Open")
    else:
        SavingFactory(
            saving_type=SavingTypeFactory(title="Open", type="pensions"), price=100000
        )

    content = client_logged.get(reverse("bookkeeping:pensions")).content.decode()

    assert row_cells(content, "Open")[8:] == ["-"] * 4


def test_pensions_queries_do_not_grow_with_closed_types(client_logged):
    def queries_with(types):
        while SavingType.objects.count() < types:
            i = SavingType.objects.count()
            _pension_type_with_a_sell(f"Fund {i}", closed=1999 if i % 2 else None)
            PensionFactory(pension_type=PensionTypeFactory(title=f"P {i}"))
        with CaptureQueriesContext(connection) as ctx:
            client_logged.get(reverse("bookkeeping:pensions"))
        return len(ctx)

    assert queries_with(2) == queries_with(6)
