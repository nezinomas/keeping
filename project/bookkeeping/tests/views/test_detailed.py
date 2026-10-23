import re
from datetime import date

import factory
import pytest
from django.db import connection
from django.db.models.signals import post_save
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, reverse

from ....core.tests.utils import clean_content
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ...tabs import TABS

pytestmark = pytest.mark.django_db

HTMX = {"hx-request": "true"}


def _expense(name, price, expense_type, month=1):
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
    assert re.search(rf'id="tab-{tab.name}"[^>]*hx-get="{tab.url}"', content)


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_view_detailed_tab_fragment_has_no_subnav(client_logged, tab):
    response = client_logged.get(tab.url, headers=HTMX)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'class="subnav"' not in content
    assert "<html" not in content
    assert f"<title>Detali | {tab.title}</title>" in content


@pytest.mark.parametrize("headers", [HTMX, {}], ids=["fragment", "page"])
def test_view_detailed_only_the_open_tab_reloads(client_logged, headers):
    content = client_logged.get("/detailed/savings/", headers=headers).content.decode()

    listener = (
        'hx-get="/detailed/savings/" hx-target="#tab_content" '
        'hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count(" from:body") == 1


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


@factory.django.mute_signals(post_save)
def test_view_detailed_opens_on_incomes(client_logged):
    IncomeFactory()
    SavingFactory()

    response = client_logged.get(reverse("bookkeeping:detailed"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Pajamos" in clean_content(content)
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
    assert '<th class="text-left title-col">' in content
    assert '<th class="month-table__total">' in content
    assert '<tr class="main__total">' in content
    assert "month-table__total" in content
    assert "left-thick-border" not in content
    assert "Išlaidos / " not in content


@pytest.mark.parametrize(
    "url_name",
    [
        pytest.param("bookkeeping:detailed", id="incomes"),
        pytest.param("bookkeeping:detailed_savings", id="savings"),
        pytest.param("bookkeeping:detailed_expenses", id="expenses"),
    ],
)
def test_view_detailed_tab_without_rows_shows_the_alert(client_logged, url_name):
    response = client_logged.get(reverse(url_name))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert '<div class="alert">' in content
    assert "metais įrašų nėra." in content
    assert "<table" not in content
    assert "<th>Taupymas</th>" not in clean_content(content)
    assert "Išlaidos / " not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_income_sorted_by_march(client_logged):
    IncomeFactory(income_type=IncomeTypeFactory(title="Aaa"), price=20)
    IncomeFactory(
        income_type=IncomeTypeFactory(title="Bbb"), price=9, date=date(1999, 3, 1)
    )
    url = reverse("bookkeeping:detailed_incomes")

    content = client_logged.get(f"{url}?order=3", headers=HTMX).content.decode()

    first, second = _positions(content, "Bbb", "Aaa")
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_every_header_sorts_but_the_shown_one(client_logged):
    IncomeFactory()
    url = "/detailed/incomes/"
    keys = ["title", *map(str, range(1, 13)), "total_col"]

    for order in keys:
        content = client_logged.get(url, {"order": order}).content.decode()

        expected = [
            f'<a role="button" hx-get="{url}?order={key}" hx-target="#tab_content">'
            for key in keys
        ]
        expected[keys.index(order)] = "<span>"
        assert re.findall(r"<th[^>]*>\s*(<span>|<a [^>]*>)", content) == expected


@pytest.mark.parametrize(
    "tab, url_name",
    [
        pytest.param("incomes", "bookkeeping:detailed_incomes", id="incomes"),
        pytest.param("savings", "bookkeeping:detailed_savings", id="savings"),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_headers_sort_through_the_tab(client_logged, tab, url_name):
    ADD_ROW[tab](1)
    url = reverse(url_name)

    content = client_logged.get(url).content.decode()

    assert f'hx-get="{url}?order=3" hx-target="#tab_content"' in content
    assert f'hx-get="{url}?order=title" hx-target="#tab_content"' in content
    assert f'hx-get="{url}?order=total_col"' not in content


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
    _expense("Alpha", 1, ExpenseTypeFactory())
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
    _expense("Alpha", 1, ExpenseTypeFactory())
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    target = "#detailed-expense-type-table"
    assert f'hx-get="{url}?order=3" hx-target="{target}"' in content
    assert f'hx-get="{url}?order=title" hx-target="{target}"' in content
    assert f'hx-get="{url}?order=total_col"' not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_sort_target_sits_inside_the_panel(client_logged):
    _expense("Alpha", 1, ExpenseTypeFactory())

    content = client_logged.get(
        reverse("bookkeeping:detailed_expenses")
    ).content.decode()

    panel, wrapper = _positions(
        content,
        'id="detailed-expense-type">',
        '<div class="month-table" id="detailed-expense-type-table">',
    )
    assert panel < wrapper < content.index("<table")


@pytest.mark.parametrize(
    "order, aaa_price, month",
    [
        pytest.param("total_col", 1, 1, id="total"),
        pytest.param("3", 20, 3, id="march"),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_type_sorted_by_column(client_logged, order, aaa_price, month):
    expense_type = ExpenseTypeFactory()
    _expense("Aaa", aaa_price, expense_type)
    _expense("Bbb", 9, expense_type, month=month)
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    response = client_logged.get(f"{url}?order={order}", headers=HTMX)
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
    _expense("Alpha", 1, ExpenseTypeFactory())
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    fragment = client_logged.get(url, headers=HTMX).content.decode()

    assert 'id="detailed-' not in fragment
    assert "month-table" in fragment
    assert 'hx-target="#detailed-expense-type-table"' in fragment
    assert '<div class="month-table"' not in fragment
    assert 'class="panel' not in fragment


def test_view_detailed_type_without_rows_renders_nothing(client_logged):
    ExpenseTypeFactory()
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    content = client_logged.get(url).content.decode("utf-8")

    assert content.strip() == ""


def test_view_detailed_type_302(client):
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    assert client.get(url).status_code == 302


def _expenses_page(client):
    return client.get(reverse("bookkeeping:detailed_expenses")).content.decode()


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_render_no_cards(client_logged):
    _expense("a1", 30000, expense_type=ExpenseTypeFactory(title="A"))
    _expense("b1", 70000, expense_type=ExpenseTypeFactory(title="B"))

    content = _expenses_page(client_logged)

    assert 'class="stat-cards"' not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_bigger_type_first(client_logged):
    _expense("a1", 30000, expense_type=ExpenseTypeFactory(title="A"))
    _expense("b1", 70000, expense_type=ExpenseTypeFactory(title="B"))

    content = _expenses_page(client_logged)

    first, second = _positions(content, 'id="detailed-b"', 'id="detailed-a"')
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_panels_carry_their_share(client_logged):
    _expense("a1", 30000, expense_type=ExpenseTypeFactory(title="A"))
    _expense("b1", 70000, expense_type=ExpenseTypeFactory(title="B"))

    content = _expenses_page(client_logged)

    assert '<p class="panel__subtitle">30% metų sumos</p>' in content
    assert '<p class="panel__subtitle">70% metų sumos</p>' in content


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_small_share_reads_less_than_one(client_logged):
    _expense("a1", 10, expense_type=ExpenseTypeFactory(title="A"))
    _expense("b1", 9990, expense_type=ExpenseTypeFactory(title="B"))

    content = _expenses_page(client_logged)

    assert '<p class="panel__subtitle">&lt; 1% metų sumos</p>' in content
    assert ">0% metų sumos" not in content


@pytest.mark.parametrize(
    "tab, url_name",
    [
        pytest.param("incomes", "bookkeeping:detailed_incomes", id="incomes"),
        pytest.param("savings", "bookkeeping:detailed_savings", id="savings"),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_other_tabs_render_no_shares(client_logged, tab, url_name):
    ADD_ROW[tab](1)

    content = client_logged.get(reverse(url_name)).content.decode()

    assert "panel__subtitle" not in content
