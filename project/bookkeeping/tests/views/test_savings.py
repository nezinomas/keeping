from datetime import date, datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ... import views
from ..factories import SavingWorthFactory
from ..helper import (
    fund_with_a_sell,
    row_cells,
    switch_a_into_b,
    total_cells,
    view_queries,
    worth_in_1999,
)

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve("/bookkeeping/savings/")

    assert views.Savings == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context(client_logged):
    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.context

    assert actual["title"] == "Fondai"
    assert actual["type"] == "savings"
    assert "object_list" in actual
    assert "total_row" in actual


def test_view_context_no_pensions_type(client_logged):
    SavingFactory(saving_type=SavingTypeFactory(title="FFF", type="funds"))
    SavingFactory(saving_type=SavingTypeFactory(title="PPP", type="pensions"))

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.context["object_list"]

    assert len(actual) == 1
    assert actual[0].saving_type.title == "FFF"


def test_percentage_from_incomes(client_logged):
    IncomeFactory(price=10)
    SavingFactory(price=20)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Pajamų dalis pervedama taupymui: <b>200,0</b>%" in actual


@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_percentage_from_incomes_reads_the_invested_price(client_logged, fee_source):
    IncomeFactory(price=10000)
    SavingFactory(
        price=2000,
        fee=500,
        saving_type=SavingTypeFactory(title="Fund", fee_source=fee_source),
    )

    actual = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert "Pajamų dalis pervedama taupymui: <b>20,0</b>%" in actual


def test_percentage_from_incomes_green_alert(client_logged):
    IncomeFactory(price=10)
    SavingFactory(price=1)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "alert alert-success" in actual


def test_percentage_from_incomes_yellow_alert(client_logged):
    IncomeFactory(price=100)
    SavingFactory(price=1)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "alert alert-warning" in actual


def test_table_percentage(client_logged):
    IncomeFactory(price=1000)
    SavingFactory(price=660)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "6,60</td>" in actual  # row
    assert "6,60</th>" in actual  # total_row


def test_percentage_from_incomes_red_alert(client_logged):
    IncomeFactory(price=10)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "alert alert-danger" in actual


def test_latest_check(client_logged):
    SavingFactory()
    SavingWorthFactory()
    SavingWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    object_list = response.context["object_list"]

    assert object_list[0].latest_check == datetime(1999, 1, 1, 1, 3, 4, tzinfo=pytz.utc)


def test_regenerate_buttons(client_logged):
    SavingFactory()

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{url}?type=savings"' in content
    assert "Bus atnaujinti tik šios lentelės balansai." in content


def test_closed_fund_with_a_sell_shows_its_profit_but_no_worth(client_logged):
    fund_with_a_sell("Closed", 100000, 60000, closed=1999)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()
    cells = row_cells(content, "Closed")

    assert cells[8:10] == ["-", "-"]
    assert cells[10] == "-400,00"
    assert cells[11] == "-40,00%"


@pytest.mark.parametrize("sold", [True, False])
def test_open_fund_with_no_worth_shows_dashes(client_logged, sold):
    if sold:
        fund_with_a_sell("Open", 100000, 60000)
    else:
        SavingFactory(saving_type=SavingTypeFactory(title="Open"), price=100000)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert row_cells(content, "Open")[8:] == ["-"] * 4


def test_savings_queries_do_not_grow_with_closed_funds(client_logged):
    def build(i):
        fund_with_a_sell(f"Fund {i}", 100000, 60000, closed=1999 if i % 2 else None)

    queries = [
        view_queries(client_logged, "bookkeeping:savings", build, n) for n in (2, 6)
    ]

    assert queries[0] == queries[1]


@pytest.mark.parametrize("kind", ["funds", "shares"])
def test_total_counts_the_switched_money_once(client_logged, kind):
    switch_a_into_b(kind=kind)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()
    cells = total_cells(content)

    assert cells[5] == "2.300,00"
    assert cells[-1] == "7,69%"


def test_total_keeps_the_base_of_a_source_closed_before_the_year(client_logged):
    a = SavingTypeFactory(title="A", closed=1998)
    b = SavingTypeFactory(title="B")
    SavingFactory(saving_type=a, price=100000, date=date(1998, 1, 1))
    SavingChangeFactory(
        from_account=a, to_account=b, price=130000, fee=0, date=date(1998, 6, 1)
    )
    worth_in_1999(b, 140000)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert total_cells(content)[-1] == row_cells(content, "B")[-1]


def test_total_counts_money_switched_through_a_closed_fund_once(client_logged):
    a = SavingTypeFactory(title="A")
    b = SavingTypeFactory(title="B", closed=1998)
    c = SavingTypeFactory(title="C")
    SavingFactory(saving_type=a, price=100000, fee=0, date=date(1998, 1, 1))
    for source, target in ((a, b), (b, c)):
        SavingChangeFactory(
            from_account=source,
            to_account=target,
            price=50000,
            fee=0,
            date=date(1998, 6, 1),
        )
    worth_in_1999(a, 50000)
    worth_in_1999(c, 60000)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert total_cells(content)[-1] == "10,00%"


def test_total_takes_off_the_gain_a_closed_fund_passes_on(client_logged):
    a = SavingTypeFactory(title="A", closed=1998)
    b = SavingTypeFactory(title="B")
    c = SavingTypeFactory(title="C")
    SavingFactory(saving_type=c, price=100000, fee=0, date=date(1998, 1, 1))
    for source, target, price in ((c, a, 40000), (a, b, 50000)):
        SavingChangeFactory(
            from_account=source,
            to_account=target,
            price=price,
            fee=0,
            date=date(1998, 6, 1),
        )
    worth_in_1999(c, 70000)
    worth_in_1999(b, 55000)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert total_cells(content)[-1] == "15,00%"


def test_total_without_switches_reads_the_plain_percentage(client_logged):
    fund = SavingTypeFactory(title="A")
    SavingFactory(saving_type=fund, price=100000, fee=0, date=date(1999, 1, 1))
    worth_in_1999(fund, 130000)

    content = client_logged.get(reverse("bookkeeping:savings")).content.decode()

    assert total_cells(content)[-1] == "30,00%"


def test_savings_queries_do_not_grow_with_switches(client_logged):
    def build(i):
        a = fund_with_a_sell(f"A {i}", 100000, 60000)
        b = SavingTypeFactory(title=f"B {i}")
        SavingChangeFactory(
            from_account=a, to_account=b, price=1000, fee=0, date=date(1999, 7, 1)
        )

    queries = [
        view_queries(client_logged, "bookkeeping:savings", build, n) for n in (2, 6)
    ]

    assert queries[0] == queries[1]
