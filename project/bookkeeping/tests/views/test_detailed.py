from datetime import date

import factory
import pytest
from django.db import connection
from django.db.models.signals import post_save
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, resolve, reverse

from ....core.tests.utils import clean_content
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ... import views
from ...tabs import TABS

pytestmark = pytest.mark.django_db

HTMX = {"hx-request": "true"}


def _expense(name, price, month=1, expense_type=None):
    expense_type = expense_type or ExpenseTypeFactory()
    ExpenseFactory(
        date=date(1999, month, 1),
        price=price,
        expense_type=expense_type,
        expense_name=ExpenseNameFactory(title=name, parent=expense_type),
    )


def _income(i):
    IncomeFactory(income_type=IncomeTypeFactory(title=f"Type {i}"))


def _saving(i):
    SavingFactory(saving_type=SavingTypeFactory(title=f"Type {i}"))


def _expense_of_type(i):
    _expense(f"Name {i}", 1, expense_type=ExpenseTypeFactory(title=f"Type {i}"))


ADD_ROW = {"incomes": _income, "savings": _saving, "expenses": _expense_of_type}


def _positions(content, *titles):
    return [content.index(title) for title in titles]


# ----------------------------------------------------------------------------
#                                                                         urls
# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "path, view",
    [
        ("/detailed/", views.TabIncomes),
        ("/detailed/incomes/", views.TabIncomes),
        ("/detailed/savings/", views.TabSavings),
        ("/detailed/expenses/", views.TabExpenses),
        ("/detailed/expenses/some-type/", views.DetailedTable),
    ],
)
def test_view_detailed_func(path, view):
    assert view == resolve(path).func.view_class


@pytest.mark.parametrize(
    "path",
    [
        "/detailed/expense-type/",
        "/detailed/income/",
        "/detailed/saving/",
        "/detailed/income/-1/",
    ],
)
def test_view_detailed_old_and_unknown_urls_404(client_logged, path):
    ExpenseFactory()

    assert client_logged.get(path).status_code == 404


def test_view_detailed_table_url_is_gone():
    with pytest.raises(NoReverseMatch):
        reverse("bookkeeping:detailed_table", kwargs={"category": "income"})


# ----------------------------------------------------------------------------
#                                                                         tabs
# ----------------------------------------------------------------------------
def test_view_detailed_200(client_logged):
    response = client_logged.get(reverse("bookkeeping:detailed"))

    assert response.status_code == 200


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_view_detailed_tab_302(client, tab):
    assert client.get(tab.url).status_code == 302


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_view_detailed_tab_page_has_the_subnav(client_logged, tab):
    response = client_logged.get(tab.url)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'class="subnav"' in content
    assert f"x-data=\"{{ tab: '{tab.name}' }}\"" in content
    assert f"<title>Detali | {tab.title}</title>" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_view_detailed_tab_fragment_has_no_subnav(client_logged, tab):
    response = client_logged.get(tab.url, headers=HTMX)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'class="subnav"' not in content
    assert "<html" not in content
    assert f"<title>Detali | {tab.title}</title>" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_view_detailed_tab_query_count_does_not_grow(client_logged, tab):
    def queries():
        with CaptureQueriesContext(connection) as captured:
            client_logged.get(tab.url)
        return len(captured)

    with factory.django.mute_signals(post_save):
        for i in range(2):
            ADD_ROW[tab.name](i)
        two = queries()

        for i in range(2, 6):
            ADD_ROW[tab.name](i)
        six = queries()

    assert two == six


def test_view_detailed_page_wears_the_paper_bundle(client_logged):
    content = client_logged.get(reverse("bookkeeping:detailed")).content.decode()

    assert "paper.min.css" in content
    assert "main.min.css" not in content
    assert 'class="paper-skin"' in content


def test_view_detailed_page_has_no_quick_add(client_logged):
    content = client_logged.get(reverse("bookkeeping:detailed")).content.decode()

    assert "quick-add" not in content


# ----------------------------------------------------------------------------
#                                                                     Pajamos
# ----------------------------------------------------------------------------
@factory.django.mute_signals(post_save)
def test_view_detailed_with_incomes(client_logged):
    IncomeFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = clean_content(response.content.decode("utf-8"))

    assert "Pajamos" in content
    assert "Income Type" in content


@factory.django.mute_signals(post_save)
def test_view_detailed_opens_on_incomes(client_logged):
    IncomeFactory()
    SavingFactory()

    content = client_logged.get(reverse("bookkeeping:detailed")).content.decode()

    assert "Income Type" in content
    assert content.count("<table") == 1


@factory.django.mute_signals(post_save)
def test_view_detailed_incomes_table_shape(client_logged):
    IncomeFactory()

    content = client_logged.get(
        reverse("bookkeeping:detailed_incomes")
    ).content.decode()

    assert '<div class="month-table">' in content
    assert content.count("<table") == 1
    assert (
        '<a role="button" hx-get="/detailed/incomes/?order=1" hx-target="#tab_content">'
        '<span class="month-table__month-full">Sausis</span>'
        '<span class="month-table__month-short">sau</span></a>'
    ) in content
    assert '<tr class="main__total">' in content
    assert "month-table__total" in content
    assert "left-thick-border" not in content
    assert "Išlaidos / " not in content


def test_view_detailed_no_incomes(client_logged):
    content = client_logged.get(reverse("bookkeeping:detailed")).content.decode()

    assert '<div class="alert">' in content
    assert "metais įrašų nėra." in content
    assert "<table" not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_income_sorted_by_march(client_logged):
    IncomeFactory(income_type=IncomeTypeFactory(title="Aaa"), price=1)
    IncomeFactory(
        income_type=IncomeTypeFactory(title="Bbb"), price=9, date=date(1999, 3, 1)
    )
    url = reverse("bookkeeping:detailed_incomes")

    content = client_logged.get(f"{url}?order=3", headers=HTMX).content.decode()

    first, second = _positions(content, "Bbb", "Aaa")
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_income_headers_sort_through_the_tab(client_logged):
    IncomeFactory()
    url = reverse("bookkeeping:detailed_incomes")

    content = client_logged.get(url).content.decode()

    assert f'hx-get="{url}?order=3" hx-target="#tab_content"' in content
    assert f'hx-get="{url}?order=total_col" hx-target="#tab_content"' in content
    assert f'hx-get="{url}?order=title"' not in content


# ----------------------------------------------------------------------------
#                                                                     Taupymas
# ----------------------------------------------------------------------------
@factory.django.mute_signals(post_save)
def test_view_detailed_with_savings(client_logged):
    SavingFactory()
    IncomeFactory()

    content = client_logged.get(
        reverse("bookkeeping:detailed_savings")
    ).content.decode()

    assert "Savings" in clean_content(content)
    assert "Taupymas" in clean_content(content)
    assert "Income Type" not in content


def test_view_detailed_no_savings(client_logged):
    content = client_logged.get(
        reverse("bookkeeping:detailed_savings")
    ).content.decode()

    assert '<div class="alert">' in content
    assert "<table" not in content
    assert "<th>Taupymas</th>" not in clean_content(content)


@factory.django.mute_signals(post_save)
def test_view_detailed_saving_headers_sort_through_the_tab(client_logged):
    SavingFactory()
    url = reverse("bookkeeping:detailed_savings")

    content = client_logged.get(url).content.decode()

    assert f'hx-get="{url}?order=3" hx-target="#tab_content"' in content


# ----------------------------------------------------------------------------
#                                                                     Išlaidos
# ----------------------------------------------------------------------------
@factory.django.mute_signals(post_save)
def test_view_detailed_rendered_expenses(client_logged, expenses):
    response = client_logged.get(reverse("bookkeeping:detailed_expenses"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Expense Name" in content
    assert "Expense Type" in content
    assert "Išlaidos / " not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_one_panel_per_type(client_logged):
    _expense("Alpha", 1, expense_type=ExpenseTypeFactory(title="Beta"))
    _expense("Omega", 1, expense_type=ExpenseTypeFactory(title="Zeta"))

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    assert content.count('class="panel panel--table"') == 2
    assert '<section class="panel panel--table" id="detailed-beta">' in content
    assert '<section class="panel panel--table" id="detailed-zeta">' in content
    assert '<h2 class="panel__title">Beta</h2>' in content
    assert '<h2 class="panel__title">Zeta</h2>' in content
    assert "Išlaidos / " not in content
    first, second = _positions(content, 'id="detailed-beta"', 'id="detailed-zeta"')
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_tab_holds_no_income_or_saving_table(client_logged):
    _expense("Alpha", 1)
    IncomeFactory()
    SavingFactory()

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    assert content.count("<table") == 1
    assert "Income Type" not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_escapes_expense_name(client_logged):
    ExpenseFactory(expense_name=ExpenseNameFactory(title="A <b>B</b>"))

    url = reverse("bookkeeping:detailed_expenses")
    content = client_logged.get(url).content.decode("utf-8")

    assert "A &lt;b&gt;B&lt;/b&gt;" in content
    assert "<b>B</b>" not in content


def test_view_detailed_no_expenses(client_logged):
    response = client_logged.get(reverse("bookkeeping:detailed_expenses"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Išlaidos / " not in content
    assert '<div class="alert">' in content


def test_view_detailed_no_expenses_with_types(client_logged):
    ExpenseTypeFactory()

    response = client_logged.get(reverse("bookkeeping:detailed_expenses"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Išlaidos / Expense Type" not in content
    assert 'id="detailed-expense-type"' not in content
    assert '<div class="alert">' in content


@factory.django.mute_signals(post_save)
def test_view_detailed_headers_sort_their_own_table(client_logged):
    _expense("Alpha", 1)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    target = "#detailed-expense-type-table"
    assert f'hx-get="{url}?order=3" hx-target="{target}"' in content
    assert f'hx-get="{url}?order=total_col" hx-target="{target}"' in content
    assert f'hx-get="{url}?order=title"' not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_sort_target_sits_inside_the_panel(client_logged):
    _expense("Alpha", 1)

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    panel, wrapper = _positions(
        content,
        'id="detailed-expense-type">',
        '<div class="month-table" id="detailed-expense-type-table">',
    )
    assert panel < wrapper < content.index("<table")


# ----------------------------------------------------------------------------
#                                                                   Type table
# ----------------------------------------------------------------------------
@factory.django.mute_signals(post_save)
def test_view_detailed_type_sorted_by_total(client_logged):
    _expense("Aaa", 1)
    _expense("Bbb", 9)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    response = client_logged.get(f"{url}?order=total_col", headers=HTMX)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert content.count("<table") == 1
    first, second = _positions(content, "Bbb", "Aaa")
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_type_sorted_by_march(client_logged):
    _expense("Aaa", 1)
    _expense("Bbb", 9, month=3)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    response = client_logged.get(f"{url}?order=3", headers=HTMX)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert content.count("<table") == 1
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
def test_view_detailed_type_fragment_is_the_bare_table(client_logged):
    _expense("Alpha", 1)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    fragment = client_logged.get(url, headers=HTMX).content.decode()

    assert 'id="detailed-' not in fragment
    assert "month-table" in fragment
    assert 'hx-target="#detailed-expense-type-table"' in fragment
    assert '<div class="month-table"' not in fragment
    assert 'class="panel' not in fragment


def test_view_detailed_type_no_data(client_logged):
    ExpenseTypeFactory()
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    assert client_logged.get(url).status_code == 200


def test_view_detailed_type_302(client):
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    assert client.get(url).status_code == 302
