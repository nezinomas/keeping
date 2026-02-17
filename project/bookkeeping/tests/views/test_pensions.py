from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ....pensions.tests.factories import PensionFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ... import views
from ..factories import PensionWorthFactory

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
