from datetime import date, datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ... import views
from ..factories import PensionWorthFactory
from ..helper import (
    fund_with_a_sell,
    row_cells,
    switch_a_into_b,
    total_cells,
    view_queries,
)

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

    url = reverse("bookkeeping:regenerate_balances")

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
    def build(i):
        _pension_type_with_a_sell(f"Fund {i}", closed=1999 if i % 2 else None)
        PensionFactory(pension_type=PensionTypeFactory(title=f"P {i}"))

    queries = [
        view_queries(client_logged, "bookkeeping:pensions", build, n) for n in (2, 6)
    ]

    assert queries[0] == queries[1]


def test_total_counts_the_switched_money_once(client_logged):
    switch_a_into_b(kind="pensions")

    content = client_logged.get(reverse("bookkeeping:pensions")).content.decode()
    cells = total_cells(content)

    assert cells[5] == "2.300,00"
    assert cells[-1] == "7,69%"


def test_total_ignores_a_switch_between_funds(client_logged):
    switch_a_into_b(kind="funds")
    PensionFactory(price=100000)
    PensionWorthFactory(price=130000)

    content = client_logged.get(reverse("bookkeeping:pensions")).content.decode()

    assert total_cells(content)[5] == "1.000,00"
    assert total_cells(content)[-1] == row_cells(content, "PensionType")[-1]


def test_pensions_queries_do_not_grow_with_switches(client_logged):
    def build(i):
        a = _pension_type_with_a_sell(f"A {i}")
        b = SavingTypeFactory(title=f"B {i}", type="pensions")
        SavingChangeFactory(
            from_account=a, to_account=b, price=1000, fee=0, date=date(1999, 7, 1)
        )

    queries = [
        view_queries(client_logged, "bookkeeping:pensions", build, n) for n in (2, 6)
    ]

    assert queries[0] == queries[1]
