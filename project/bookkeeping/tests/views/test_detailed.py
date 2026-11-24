import re
from datetime import date

import factory
import pytest
from django.db import connection
from django.db.models.signals import post_save
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ...tabs import DETAILED_TABS

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


TITLE_COLUMN = r"<tr>\s*<th>\s*<a [^>]*>{title}</a>"
ROW_TITLE = "<td>{title}</td>"


def _positions(content, *titles):
    return [content.index(title) for title in titles]


def test_view_detailed_sends_a_visitor_to_the_login(client):
    response = client.get("/detailed/")

    assert response.status_code == 302
    assert response.url == "/login/?next=/detailed/"


@pytest.mark.parametrize(
    "headers, page",
    [pytest.param({}, True, id="page"), pytest.param(HTMX, False, id="fragment")],
)
def test_view_detailed_tab_url_draws_its_page_plainly_and_its_fragment_to_htmx(
    client_logged, headers, page
):
    content = client_logged.get("/detailed/savings/", headers=headers).content.decode()

    drawn = {
        "subnav": '<nav class="subnav">' in content,
        "any subnav mark": 'class="subnav"' in content,
        "html": "<html" in content,
        "open tab": "x-data=\"{ tab: 'savings' }\"" in content,
        "tab button": bool(
            re.search(r'id="tab-savings"[^>]*hx-get="/detailed/savings/"', content)
        ),
    }
    assert drawn == dict.fromkeys(drawn, page)
    assert "<title>Detali | Taupymas</title>" in content


@pytest.mark.parametrize(
    "url, title",
    [
        pytest.param("/detailed/incomes/", "Pajamos", id="incomes"),
        pytest.param("/detailed/savings/", "Taupymas", id="savings"),
        pytest.param("/detailed/expenses/", "Išlaidos", id="expenses"),
    ],
)
def test_view_detailed_browser_title_names_the_open_tab(client_logged, url, title):
    content = client_logged.get(url).content.decode()

    assert f"<title>Detali | {title}</title>" in content


def test_view_detailed_only_the_open_tab_reloads(client_logged):
    content = client_logged.get("/detailed/savings/").content.decode()

    listener = (
        'hx-get="/detailed/savings/" hx-target="#tab_content" '
        'hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count(" from:body") == 1


@pytest.mark.parametrize("tab", DETAILED_TABS, ids=lambda tab: tab.name)
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

    assert '<link rel="stylesheet" href="/static/css/paper.min.css">' in content
    assert '<link rel="stylesheet" href="/static/css/main.min.css">' not in content
    assert 'class="paper-skin"' in content
    assert not re.search(r'class="(?:[^"]* )?quick-add[" ]', content)


@pytest.mark.parametrize(
    "url_name, tab, title, rows, panels",
    [
        pytest.param(
            "bookkeeping:detailed",
            "incomes",
            "Pajamos",
            ["Income Type"],
            [],
            id="opens",
        ),
        pytest.param(
            "bookkeeping:detailed_savings",
            "savings",
            "Taupymas",
            ["Savings"],
            [],
            id="savings",
        ),
        pytest.param(
            "bookkeeping:detailed_expenses",
            "expenses",
            "Expense Type",
            ["Alpha"],
            ["Expense Type"],
            id="expenses",
        ),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_tab_is_open_and_holds_only_its_own_table(
    client_logged, url_name, tab, title, rows, panels
):
    IncomeFactory()
    SavingFactory()
    _expense("Alpha", 1, ExpenseTypeFactory())

    content = client_logged.get(reverse(url_name)).content.decode()

    assert re.findall(r"x-data=\"\{ tab: '(\w+)' \}\"", content) == [tab]
    assert re.findall(TITLE_COLUMN.format(title="([^<]*)"), content) == [title]
    assert re.findall(ROW_TITLE.format(title="([^<]*)"), content) == [*rows, "Viso"]
    assert re.findall(r'<h2 class="panel__title">([^<]*)</h2>', content) == panels
    assert content.count("<table") == 1


@factory.django.mute_signals(post_save)
def test_view_detailed_table_has_a_title_column_and_a_total_column_and_row(
    client_logged,
):
    IncomeFactory()

    content = client_logged.get("/detailed/incomes/").content.decode()

    assert re.search(r'<div class="month-table">\s*<table class="main ', content)
    assert re.findall(TITLE_COLUMN.format(title="([^<]*)"), content) == ["Pajamos"]
    assert re.search(r'<th class="month-table__total">\s*<span>Viso</span>', content)
    assert re.search(r'<tfoot>\s*<tr class="main__total">\s*<td>Viso</td>', content)
    assert content.count('<td class="main__figure month-table__total">') == 2


@factory.django.mute_signals(post_save)
def test_view_detailed_total_row_sums_its_rows(client_logged):
    IncomeFactory(price=110, income_type=IncomeTypeFactory(title="Aaa"))
    IncomeFactory(price=225, income_type=IncomeTypeFactory(title="Bbb"))

    content = client_logged.get("/detailed/incomes/").content.decode()

    total_row = re.search(r"<tfoot>(.*?)</tfoot>", content, re.S).group(1)
    figures = re.findall(
        r'<td class="main__figure[^"]*"[^>]*>\s*(\S+)\s*</td>', total_row
    )
    assert (figures[0], figures[-1]) == ("3,35", "3,35")


@factory.django.mute_signals(post_save)
def test_view_detailed_one_income_leaves_its_other_months_empty(client_logged):
    IncomeFactory()

    content = client_logged.get("/detailed/incomes/").content.decode()

    # eleven empty months in its row and in the total row
    assert content.count('<td class="main__figure" data-cell="empty">') == 22


def test_view_detailed_heads_the_months_with_the_quarter_band(client_logged):
    IncomeFactory()

    content = client_logged.get(
        reverse("bookkeeping:detailed_incomes")
    ).content.decode()

    head = content.split("<thead")[1].split("</thead>")[0]
    band, months = re.findall(r"<tr[^>]*>(.*?)</tr>", head, re.S)
    quarter = ' class="month-table__quarter" colspan="3"'
    assert re.findall(r"<(?:a [^>]*|span)>(.*?)</", months) == [
        "Pajamos", "Saus.", "Vas.", "Kov.", "Bal.", "Geg.", "Birž.",
        "Liep.", "Rugp.", "Rugs.", "Spal.", "Lapkr.", "Gruod.", "Viso",
    ]  # fmt: skip
    assert re.findall(r"<th([^>]*)>(.*?)</th>", band) == [
        ("", ""),
        (quarter, "I ketv."),
        (quarter, "II ketv."),
        (quarter, "III ketv."),
        (quarter, "IV ketv."),
        ("", ""),
    ]


@pytest.mark.parametrize(
    "url_name",
    [
        pytest.param("bookkeeping:detailed", id="incomes"),
        pytest.param("bookkeeping:detailed_expenses", id="expenses"),
    ],
)
def test_view_detailed_tab_without_rows_shows_the_alert(client_logged, url_name):
    ExpenseTypeFactory()

    content = client_logged.get(reverse(url_name)).content.decode("utf-8")

    assert re.search(r'<div class="alert">\s*1999 metais įrašų nėra\.', content)
    assert "<table" not in content
    assert '<section class="panel' not in content


SORT_KEYS = ["title", *map(str, range(1, 13)), "total_col"]


@pytest.mark.parametrize("order", SORT_KEYS)
@factory.django.mute_signals(post_save)
def test_view_detailed_every_header_sorts_but_the_shown_one(client_logged, order):
    IncomeFactory()
    url = "/detailed/incomes/"

    content = client_logged.get(url, {"order": order}).content.decode()

    expected = [
        f'<a role="button" hx-get="{url}?order={key}" hx-target="#tab_content">'
        for key in SORT_KEYS
    ]
    expected[SORT_KEYS.index(order)] = "<span>"
    assert re.findall(r"<th[^>]*>\s*(<span>|<a [^>]*>)", content) == expected


@factory.django.mute_signals(post_save)
def test_view_detailed_a_type_table_sorts_inside_its_own_panel(client_logged):
    _expense("Alpha", 1, ExpenseTypeFactory())

    content = client_logged.get("/detailed/expenses/").content.decode()

    link = (
        '<a role="button" hx-get="/detailed/expenses/expense-type/?order={}" '
        'hx-target="#detailed-expense-type-table">'
    )
    assert link.format(3) in content
    assert link.format("title") in content
    assert link.format("total_col") not in content


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


@factory.django.mute_signals(post_save)
def test_view_detailed_escapes_expense_name(client_logged):
    ExpenseFactory(expense_name=ExpenseNameFactory(title="A <b>B</b>"))

    url = reverse("bookkeeping:detailed_expenses")
    content = client_logged.get(url).content.decode("utf-8")

    assert ROW_TITLE.format(title="A &lt;b&gt;B&lt;/b&gt;") in content
    assert "<b>B</b>" not in content


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
    first, second = _positions(
        content, ROW_TITLE.format(title="Bbb"), ROW_TITLE.format(title="Aaa")
    )
    assert first < second


@factory.django.mute_signals(post_save)
def test_view_detailed_type_slugged_income_reads_its_own_table(client_logged):
    _expense("Alpha", 1, expense_type=ExpenseTypeFactory(title="Income"))
    IncomeFactory(income_type=IncomeTypeFactory(title="Salary"))
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "income"})

    content = client_logged.get(url).content.decode("utf-8")

    assert ROW_TITLE.format(title="Alpha") in content
    assert ROW_TITLE.format(title="Salary") not in content


@factory.django.mute_signals(post_save)
def test_view_detailed_type_fragment_is_the_bare_table(client_logged):
    _expense("Alpha", 1, ExpenseTypeFactory())
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    fragment = client_logged.get(url, headers=HTMX).content.decode()

    assert 'id="detailed-' not in fragment
    assert re.match(r'\s*<table class="main striped hover">\s*<thead ', fragment)
    assert '<td class="main__figure month-table__total">' in fragment
    assert re.search(
        r'<a role="button" hx-get="[^"]*" hx-target="#detailed-expense-type-table">',
        fragment,
    )
    assert '<div class="month-table"' not in fragment
    assert 'class="panel' not in fragment


def test_view_detailed_type_without_rows_renders_nothing(client_logged):
    ExpenseTypeFactory()
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": "expense-type"})

    content = client_logged.get(url).content.decode("utf-8")

    assert content.strip() == ""


def _expenses_page(client):
    return client.get(reverse("bookkeeping:detailed_expenses")).content.decode()


@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_render_no_cards(client_logged):
    _expense("a1", 30000, expense_type=ExpenseTypeFactory(title="A"))
    _expense("b1", 70000, expense_type=ExpenseTypeFactory(title="B"))

    content = _expenses_page(client_logged)

    assert 'class="stat-cards"' not in content


@pytest.mark.parametrize(
    "types, order",
    [
        # made in the other order, so a tie read by creation would show
        pytest.param([("Zeta", 1), ("Beta", 1)], ["beta", "zeta"], id="tie_by_title"),
        pytest.param([("A", 30000), ("B", 70000)], ["b", "a"], id="bigger_first"),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_expenses_panels_run_by_total_then_title(
    client_logged, types, order
):
    for title, price in types:
        _expense(f"{title} name", price, expense_type=ExpenseTypeFactory(title=title))

    content = _expenses_page(client_logged)

    assert (
        re.findall(r'<section class="panel panel--table" id="detailed-(\w+)">', content)
        == order
    )


def _two_types(a, b):
    def build():
        _expense("a1", a, expense_type=ExpenseTypeFactory(title="A"))
        _expense("b1", b, expense_type=ExpenseTypeFactory(title="B"))

    return build


@pytest.mark.parametrize(
    "url_name, build, shares",
    [
        pytest.param(
            "bookkeeping:detailed_expenses",
            _two_types(30000, 70000),
            ["70% metų sumos", "30% metų sumos"],
            id="whole",
        ),
        pytest.param(
            "bookkeeping:detailed_expenses",
            _two_types(10, 9990),
            ["&gt; 99% metų sumos", "&lt; 1% metų sumos"],
            id="edges",
        ),
        pytest.param("bookkeeping:detailed_incomes", IncomeFactory, [], id="incomes"),
    ],
)
@factory.django.mute_signals(post_save)
def test_view_detailed_panels_carry_a_share_only_on_expenses(
    client_logged, url_name, build, shares
):
    build()

    content = client_logged.get(reverse(url_name)).content.decode()

    assert re.findall(r'<p class="panel__subtitle">([^<]*)</p>', content) == shares
    # the bare mark too: no subtitle on any other element
    assert content.count("panel__subtitle") == len(shares)
