from datetime import date

import factory
import pytest
from django.db import connection
from django.db.models.signals import post_save
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse

from ....core.tests.utils import clean_content
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....savings.tests.factories import SavingFactory
from ... import views

pytestmark = pytest.mark.django_db


def test_view_detailed_func():
    view = resolve("/detailed/")

    assert views.Detailed == view.func.view_class


def test_view_detailed_200(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_detailed_302(client):
    url = reverse("bookkeeping:detailed")
    response = client.get(url)

    assert response.status_code == 302


@factory.django.mute_signals(post_save)
def test_view_detailed_rendered_expenses(client_logged, expenses):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Expense Name" in content
    assert "Išlaidos / Expense Type" in content


@factory.django.mute_signals(post_save)
def test_view_detailed_escapes_expense_name(client_logged):
    ExpenseFactory(expense_name=ExpenseNameFactory(title="A <b>B</b>"))

    url = reverse("bookkeeping:detailed")
    content = client_logged.get(url).content.decode("utf-8")

    assert "A &lt;b&gt;B&lt;/b&gt;" in content
    assert "<b>B</b>" not in content


def test_view_detailed_no_expenses(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / " not in content


def test_view_detailed_no_expenses_with_types(client_logged):
    ExpenseTypeFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / Expense Type" not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_with_incomes(client_logged):
    IncomeFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = clean_content(response.content.decode("utf-8"))

    assert "Pajamos" in content
    assert "Income Type" in content


def test_view_detailed_no_incomes(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "<th>Pajamos</th>" not in content
    assert "Income Type</td>" not in content


def test_view_detailed_no_savings(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = clean_content(response.content.decode("utf-8"))

    assert "<th>Taupymas</th>" not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_with_savings(client_logged):
    SavingFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = clean_content(response.content.decode("utf-8"))

    assert "Taupymas" in content
    assert "Savings" in content


@pytest.mark.parametrize(
    "path",
    ["/detailed/income/", "/detailed/saving/", "/detailed/expenses/some-type/"],
)
def test_view_detailed_table_func(path):
    assert views.DetailedTable == resolve(path).func.view_class


@pytest.mark.parametrize("path", ["/detailed/expense-type/", "/detailed/income/-1/"])
def test_view_detailed_old_and_unknown_urls_404(client_logged, path):
    ExpenseFactory()

    assert client_logged.get(path).status_code == 404


def _expense(name, price, month=1, expense_type=None):
    expense_type = expense_type or ExpenseTypeFactory()
    ExpenseFactory(
        date=date(1999, month, 1),
        price=price,
        expense_type=expense_type,
        expense_name=ExpenseNameFactory(title=name, parent=expense_type),
    )


def _positions(content, *titles):
    return [content.index(title) for title in titles]


@factory.django.mute_signals(post_save)
def test_view_detailed_type_sorted_by_total(client_logged):
    _expense("Aaa", 1)
    _expense("Bbb", 9)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    response = client_logged.get(
        f"{url}?order=total_col", headers={"hx-request": "true"}
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert content.count("<table") == 1
    first, second = _positions(content, "Bbb", "Aaa")
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_income_sorted_by_march(client_logged):
    IncomeFactory(income_type=IncomeTypeFactory(title="Aaa"), price=1)
    IncomeFactory(
        income_type=IncomeTypeFactory(title="Bbb"), price=9, date=date(1999, 3, 1)
    )
    url = reverse("bookkeeping:detailed_table", kwargs={"category": "income"})

    content = client_logged.get(f"{url}?order=3").content.decode("utf-8")

    assert "Pajamos" in content
    first, second = _positions(content, "Bbb", "Aaa")
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_type_slugged_income_reads_its_own_table(client_logged):
    _expense("Alpha", 1, expense_type=ExpenseTypeFactory(title="Income"))
    IncomeFactory(income_type=IncomeTypeFactory(title="Salary"))
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "income"})

    content = client_logged.get(url).content.decode("utf-8")

    assert "Alpha" in content
    assert "Salary" not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_headers_sort_their_own_table(client_logged):
    _expense("Alpha", 1)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    content = client_logged.get(reverse("bookkeeping:detailed")).content.decode()

    assert f'hx-get="{url}?order=3" hx-target="#tbl-expense-type"' in content
    assert f'hx-get="{url}?order=total_col"' in content
    assert f'hx-get="{url}?order=title"' not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_sort_target_wraps_the_table(client_logged):
    _expense("Alpha", 1)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    page = client_logged.get(reverse("bookkeeping:detailed")).content.decode()
    fragment = client_logged.get(url).content.decode()

    assert '<div id="tbl-expense-type">' in page
    assert 'id="tbl-' not in fragment


def test_view_detailed_type_no_data(client_logged):
    ExpenseTypeFactory()
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    assert client_logged.get(url).status_code == 200


def test_view_detailed_type_302(client):
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    assert client.get(url).status_code == 302


def _page_queries(client):
    with CaptureQueriesContext(connection) as queries:
        client.get(reverse("bookkeeping:detailed"))
    return len(queries)


@factory.django.mute_signals(post_save)
def test_view_detailed_query_count_does_not_grow_with_the_types(client_logged):
    for i in range(2):
        _expense(f"Name {i}", 1, expense_type=ExpenseTypeFactory(title=f"Type {i}"))
    two = _page_queries(client_logged)

    for i in range(2, 6):
        _expense(f"Name {i}", 1, expense_type=ExpenseTypeFactory(title=f"Type {i}"))
    six = _page_queries(client_logged)

    assert two == six
