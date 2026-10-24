import json
import re
from collections.abc import Callable
from datetime import date
from typing import NamedTuple

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.html import escape

from ...core.tests.utils import (
    count_queries,
    form_posts_to,
    nav_tabs,
    quick_add_pills,
    view_for,
)
from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...savings.tests.factories import SavingTypeFactory
from .. import forms, views
from ..services.model_services import IncomePlanModelService
from ..tabs import TABS
from .factories import (
    DayPlan,
    DayPlanFactory,
    ExpensePlan,
    ExpensePlanFactory,
    IncomePlan,
    IncomePlanFactory,
    NecessaryPlan,
    NecessaryPlanFactory,
    SavingPlan,
    SavingPlanFactory,
)

pytestmark = pytest.mark.django_db

TAB_PANEL_TITLES = {
    "incomes": ["Pajamos"],
    "expenses": [
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Kasdienės išlaidos",
    ],
    "savings": ["Taupymas"],
    "day": [
        "Suma dienai",
        "Kiek galiu išleisti per dieną",
        "Patikra: ar telpa išlaidų planai",
    ],
}

TAB_TABLE_PANELS = {
    "incomes": ["income-plans"],
    "expenses": [
        "necessary-expense-plans",
        "necessary-plans",
        "everyday-expense-plans",
    ],
    "savings": ["saving-plans"],
    "day": ["day-plans", "calculations-spend", "calculations-check"],
}

MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


class Kind(NamedTuple):
    factory: type
    model: type
    tab: str
    new: str
    update: str
    delete: str
    own_kwargs: Callable  # the url kwargs a plan adds to its year
    owner: Callable  # the rows a plan points at, as factory kwargs


INCOME = Kind(
    factory=IncomePlanFactory,
    model=IncomePlan,
    tab="plans:tab_incomes",
    new="plans:income_new",
    update="plans:income_update",
    delete="plans:income_delete",
    own_kwargs=lambda plan: {"income_type_id": plan.income_type.pk},
    owner=lambda **kwargs: {"income_type": IncomeTypeFactory(**kwargs)},
)
EXPENSE = Kind(
    factory=ExpensePlanFactory,
    model=ExpensePlan,
    tab="plans:tab_expenses",
    new="plans:expense_new",
    update="plans:expense_update",
    delete="plans:expense_delete",
    own_kwargs=lambda plan: {"expense_type_id": plan.expense_type.pk},
    owner=lambda **kwargs: {"expense_type": ExpenseTypeFactory(**kwargs)},
)
SAVING = Kind(
    factory=SavingPlanFactory,
    model=SavingPlan,
    tab="plans:tab_savings",
    new="plans:saving_new",
    update="plans:saving_update",
    delete="plans:saving_delete",
    own_kwargs=lambda plan: {"saving_type_id": plan.saving_type.pk},
    owner=lambda **kwargs: {
        "saving_type": SavingTypeFactory(title="Saving Type", **kwargs)
    },
)
DAY = Kind(
    factory=DayPlanFactory,
    model=DayPlan,
    tab="plans:tab_day",
    new="plans:day_new",
    update="plans:day_update",
    delete="plans:day_delete",
    own_kwargs=lambda plan: {},
    owner=lambda **kwargs: {},
)
NECESSARY = Kind(
    factory=NecessaryPlanFactory,
    model=NecessaryPlan,
    tab="plans:tab_expenses",
    new="plans:necessary_new",
    update="plans:necessary_update",
    delete="plans:necessary_delete",
    own_kwargs=lambda plan: {
        "expense_type_id": plan.expense_type.pk,
        "title": plan.title,
    },
    owner=lambda **kwargs: {"expense_type": ExpenseTypeFactory(**kwargs)},
)


def _form_values(owned):
    return {field: row.pk for field, row in owned.items()}


def _rendered_year(content):
    return re.search(r'<input type="text" name="year" value="(\d+)"', content).group(1)


def _rendered_months(content):
    inputs = re.findall(r'<input type="text" name="(\w+)"( value="([^"]*)")?', content)
    return {name: value for name, _, value in inputs if name in MONTHS and value}


def _select(content, field):
    return content.split(f'<select name="{field}"')[1].split("</select>")[0]


def _rendered_selected(content, field):
    select = _select(content, field)
    return re.search(r"<option [^>]*selected>([^<]*)</option>", select).group(1)


def _between(content, start_id, end_id=""):
    start = content.index(f'id="{start_id}"')
    end = len(content)
    if end_id:
        end = content.index(f'id="{end_id}"')

    return content[start:end]


def _panel(content, panel_id):
    section = _between(content, panel_id)
    return section[: section.index("</section>")]


def _row_titles(table):
    return re.findall(r'<tr[^>]*>\s*<td class="text-left">\s*(.*?)\s*</td>', table)


def _month_cells(table, figure):
    return re.findall(rf'<td class="[^"]*" data-cell="[^"]*">{figure}</td>', table)


def _assert_reload_triggered(response):
    assert json.loads(response.headers["HX-Trigger"]) == {"reload": {}}


# Tabs
def test_index_not_logged(client):
    url = reverse("plans:index")
    response = client.get(url)

    assert response.status_code == 302


def test_index_opens_the_day_tab(client_logged):
    content = client_logged.get(reverse("plans:index")).content.decode()

    assert "x-data=\"{ tab: 'day' }\"" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged, tab):
    content = client_logged.get(tab.url).content.decode()

    assert '<nav class="subnav">' in content
    assert '<link rel="stylesheet" href="/static/css/paper.min.css">' in content
    assert 'class="paper-skin"' in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_url_requested_by_htmx_returns_the_fragment_alone(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    assert '<nav class="subnav">' not in content
    assert 'class="quick-add' not in content
    assert "<title>" in content


@pytest.mark.parametrize(
    ("url_name", "title"),
    [
        ("plans:tab_incomes", "Planai | Pajamos"),
        ("plans:tab_expenses", "Planai | Išlaidos"),
        ("plans:tab_savings", "Planai | Taupymas"),
        ("plans:tab_day", "Planai | Suma dienai"),
    ],
    ids=["incomes", "expenses", "savings", "day"],
)
def test_browser_title_names_the_open_tab(client_logged, url_name, title):
    content = client_logged.get(reverse(url_name)).content.decode()

    assert f"<title>{title}</title>" in content


@pytest.mark.parametrize(
    "headers", [{"HX-Request": "true"}, {}], ids=["fragment", "page"]
)
@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_only_the_open_tab_reloads_on_a_saved_plan(client_logged, tab, headers):
    content = client_logged.get(tab.url, headers=headers).content.decode()

    listener = (
        f'hx-get="{tab.url}" hx-target="#tab_content" hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_fragment_carries_only_its_own_panel_titles(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    for title in TAB_PANEL_TITLES[tab.name]:
        assert re.search(rf'<h2 class="panel__title">{title}(</h2>| <span)', content)

    other_titles = {
        title
        for name, titles in TAB_PANEL_TITLES.items()
        if name != tab.name
        for title in titles
        if title not in TAB_PANEL_TITLES[tab.name]
    }
    for title in other_titles:
        assert not re.search(
            rf'<h2 class="panel__title">{title}(</h2>| <span)', content
        )


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_every_panel_on_a_tab_is_a_table_panel(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    for panel_id in TAB_TABLE_PANELS[tab.name]:
        assert f'<section class="panel panel--table" id="{panel_id}">' in content
    assert '<section class="panel" ' not in content


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("plans:index")).content.decode()

    assert nav_tabs(content) == [
        ("incomes", reverse("plans:tab_incomes")),
        ("expenses", reverse("plans:tab_expenses")),
        ("savings", reverse("plans:tab_savings")),
        ("day", reverse("plans:tab_day")),
    ]


# Cards
@pytest.mark.parametrize(
    "factory, url, present, absent",
    [
        (
            IncomePlanFactory,
            "plans:tab_incomes",
            ["Per metus", "Mėnesio mediana"],
            ["Šiais metais"],
        ),
        (
            SavingPlanFactory,
            "plans:tab_savings",
            ["Per metus", "Planuotų pajamų dalis", "Per mėnesį"],
            ["Šiais metais"],
        ),
        (
            ExpensePlanFactory,
            "plans:tab_expenses",
            ["Per metus", "Būtinos", "Kasdienės", "Per mėnesį"],
            ["Šiais metais", "Laisvos"],
        ),
    ],
    ids=["incomes", "savings", "expenses"],
)
def test_tab_renders_its_cards_in_lithuanian(
    factory, url, present, absent, client_logged
):
    factory(price=1000)

    content = client_logged.get(reverse(url)).content.decode()

    for label in present:
        assert f'<div class="trend-card__label">{label}</div>' in content
    for label in absent:
        assert f'<div class="trend-card__label">{label}</div>' not in content


# Bottom bar
def test_quick_add_offers_its_pills(client_logged):
    content = client_logged.get(reverse("plans:index")).content.decode()

    assert quick_add_pills(content) == [
        (
            "button",
            "expenses",
            'hx-get="/plans/expenses/new/"',
            "Pridėti išlaidų planą",
        ),
        (
            "button",
            "expenses",
            'hx-get="/plans/necessary/new/"',
            "Pridėti būtinų išlaidų planą",
        ),
        ("button", "incomes", 'hx-get="/plans/incomes/new/"', "Pridėti pajamų planą"),
        ("button", "savings", 'hx-get="/plans/savings/new/"', "Pridėti taupymo planą"),
        ("button", "day", 'hx-get="/plans/day/new/"', "Pridėti dienos planą"),
        ("button", "", 'hx-get="/plans/copy/"', "Kopijuoti planus"),
    ]


def test_the_expenses_tab_orders_necessary_extra_necessary_then_everyday(
    client_logged,
):
    content = client_logged.get(reverse("plans:tab_expenses")).content.decode()

    positions = [
        content.index(f'id="{panel}"') for panel in TAB_TABLE_PANELS["expenses"]
    ]
    assert positions == sorted(positions)


def test_the_expenses_tab_splits_the_expense_plans_by_necessity(client_logged):
    ExpensePlanFactory(expense_type=ExpenseTypeFactory(title="Būstas", necessary=True))
    ExpensePlanFactory(expense_type=ExpenseTypeFactory(title="Maistas"))

    content = client_logged.get(reverse("plans:tab_expenses")).content.decode()

    necessary = _between(content, "necessary-expense-plans", "necessary-plans")
    everyday = _between(content, "everyday-expense-plans")
    assert _row_titles(necessary) == ["Būstas"]
    assert _row_titles(everyday) == ["Maistas"]


def test_the_necessary_expenses_panel_explains_where_necessity_is_set(client_logged):
    content = client_logged.get(reverse("plans:tab_expenses")).content.decode()

    panel = content[content.index('id="necessary-expense-plans"') :]
    panel = panel[: panel.index("</h2>")]
    assert re.search(
        r'<span class="panel__hint[^"]*"[^>]* data-tip="Išlaidų tipai, pažymėti kaip'
        r' būtini[^"]*"[^>]*><i class="bi bi-question-circle"></i></span>',
        panel,
    )


# Plans of every kind
@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="income_tab_edit_delete_urls"),
        pytest.param(EXPENSE, id="expense_tab_edit_delete_urls"),
        pytest.param(SAVING, id="saving_tab_edit_delete_urls"),
        pytest.param(DAY, id="day_tab_edit_delete_urls"),
        pytest.param(NECESSARY, id="necessary_tab_edit_delete_urls"),
    ],
)
def test_plan_tab_edit_delete_urls(client_logged, main_user, kind):
    obj = kind.factory()

    response = client_logged.get(reverse(kind.tab))
    actual = response.content.decode("utf-8")

    kwargs = {"year": main_user.year, **kind.own_kwargs(obj)}
    links = re.findall(
        r'<td class="(edit|delete)-col">\s*<a role="button" hx-get="([^"]*)"', actual
    )
    assert links == [
        ("edit", reverse(kind.update, kwargs=kwargs)),
        ("delete", reverse(kind.delete, kwargs=kwargs)),
    ]


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="income_load_form"),
        pytest.param(EXPENSE, id="expense_load_form"),
        pytest.param(SAVING, id="saving_load_form"),
        pytest.param(DAY, id="day_load_form"),
        pytest.param(NECESSARY, id="necessary_load_form"),
    ],
)
def test_plan_load_form(client_logged, kind):
    url = reverse(kind.new)
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200
    assert form_posts_to(actual, "generic-form", url)
    assert 'class="modal-body plans-form"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


@pytest.mark.parametrize(
    "kind, january, price",
    [
        pytest.param(INCOME, 0.01, 1, id="income_new"),
        pytest.param(EXPENSE, 0.01, 1, id="expense_new"),
        pytest.param(SAVING, 0.01, 1, id="saving_new"),
        pytest.param(DAY, 0.05, 5, id="day_new"),
    ],
)
def test_plan_new(client_logged, main_user, kind, january, price):
    data = {"year": "1999", "january": january, **_form_values(kind.owner())}

    client_logged.post(reverse(kind.new), data, follow=True)
    actual = kind.model.objects.first()

    assert actual.journal == main_user.journal
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == price


@pytest.mark.parametrize(
    "kind, own_data, error_fields",
    [
        pytest.param(
            INCOME,
            {"income_type": 0},
            ["year", "income_type"],
            id="income_new_invalid_data",
        ),
        pytest.param(
            EXPENSE,
            {"expense_type": 0},
            ["year", "expense_type"],
            id="expense_new_invalid_data",
        ),
        pytest.param(
            SAVING,
            {"saving_type": 0},
            ["year", "saving_type"],
            id="saving_new_invalid_data",
        ),
        pytest.param(DAY, {}, ["year"], id="day_invalid_data"),
        pytest.param(
            NECESSARY, {"title": ""}, ["year", "title"], id="necessary_invalid_data"
        ),
    ],
)
def test_plan_new_invalid_data(client_logged, kind, own_data, error_fields):
    data = {"year": "x", "january": 999, **own_data}

    content = client_logged.post(reverse(kind.new), data).content.decode()

    invalid = re.findall(r'<(?:input|select)[^>]*name="(\w+)"[^>]*is-invalid', content)
    assert set(error_fields) <= set(invalid)


@pytest.mark.parametrize(
    "kind, own_data",
    [
        pytest.param(INCOME, {}, id="income_new_returns_htmx_response"),
        pytest.param(EXPENSE, {}, id="expense_new_returns_htmx_response"),
        pytest.param(SAVING, {}, id="saving_new_returns_htmx_response"),
        pytest.param(DAY, {}, id="day_new_returns_htmx_response"),
        pytest.param(
            NECESSARY, {"title": "Nuoma"}, id="necessary_new_returns_htmx_response"
        ),
    ],
)
def test_plan_new_returns_htmx_response(client_logged, kind, own_data):
    owned = kind.owner()
    data = {"year": "1999", "january": 0.01, **_form_values(owned), **own_data}

    response = client_logged.post(reverse(kind.new), data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert kind.model.objects.filter(year=1999, **owned).count() == 1
    _assert_reload_triggered(response)


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="income_load_update_load_form"),
        pytest.param(EXPENSE, id="expense_load_update_load_form"),
        pytest.param(SAVING, id="saving_load_update_load_form"),
        pytest.param(DAY, id="day_load_update_load_form"),
        pytest.param(NECESSARY, id="necessary_load_update_load_form"),
    ],
)
def test_plan_load_update_load_form(client_logged, kind):
    obj = kind.factory()

    url = reverse(kind.update, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert form_posts_to(actual, "generic-form", url)
    assert 'class="modal-body plans-form"' in actual


@pytest.mark.parametrize(
    "kind, field, title",
    [
        pytest.param(
            INCOME,
            "income_type",
            "Income Type",
            id="income_load_update_form_field_values",
        ),
        pytest.param(
            EXPENSE,
            "expense_type",
            "Expense Type",
            id="expense_load_update_form_field_values",
        ),
        pytest.param(
            SAVING,
            "saving_type",
            "Saving Type",
            id="saving_load_update_form_field_values",
        ),
    ],
)
def test_plan_load_update_form_field_values(client_logged, kind, field, title):
    obj = kind.factory(**kind.owner())

    url = reverse(kind.update, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    content = client_logged.get(url).content.decode()

    assert _rendered_year(content) == "1999"
    assert _rendered_selected(content, field) == title
    assert _rendered_months(content) == {"january": "0.01"}


@pytest.mark.parametrize(
    "kind, plan_kwargs, months",
    [
        pytest.param(
            DAY,
            {"month": 1, "price": 5},
            {"january": "0.05"},
            id="day_load_update_form_field_values",
        ),
        pytest.param(
            NECESSARY,
            {"title": "ABCD", "month": 11, "price": 1001},
            {"november": "10.01"},
            id="necessary_load_update_form_field_values",
        ),
    ],
)
def test_plan_without_type_load_update_form_field_values(
    client_logged, kind, plan_kwargs, months
):
    obj = kind.factory(year=1999, **plan_kwargs)

    url = reverse(kind.update, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    content = client_logged.get(url).content.decode()

    assert _rendered_year(content) == "1999"
    assert _rendered_months(content) == months


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="income_update"),
        pytest.param(EXPENSE, id="expense_update"),
        pytest.param(SAVING, id="saving_update"),
    ],
)
def test_plan_update(client_logged, kind):
    owned = kind.owner()
    obj = kind.factory(year=1999, **owned)

    data = {"year": "1999", "january": 0.05, **_form_values(owned)}
    url = reverse(kind.update, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    client_logged.post(url, data)
    actual = kind.model.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 5


@pytest.mark.parametrize(
    "kind, own_data",
    [
        pytest.param(INCOME, {}, id="income_update_returns_htmx_response"),
        pytest.param(EXPENSE, {}, id="expense_update_returns_htmx_response"),
        pytest.param(SAVING, {}, id="saving_update_returns_htmx_response"),
        pytest.param(DAY, {}, id="day_update_returns_htmx_response"),
        pytest.param(
            NECESSARY, {"title": "Nuoma"}, id="necessary_update_returns_htmx_response"
        ),
    ],
)
def test_plan_update_returns_htmx_response(client_logged, kind, own_data):
    owned = kind.owner()
    obj = kind.factory(year=1999, month=1, price=1000, **owned, **own_data)

    data = {"year": "1999", "january": 9.99, **_form_values(owned), **own_data}
    url = reverse(kind.update, kwargs={"year": 1999, **kind.own_kwargs(obj)})

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert kind.model.objects.get(year=1999, month=1, **owned).price == 999
    _assert_reload_triggered(response)


@pytest.mark.parametrize(
    "kind, panel, price, text",
    [
        pytest.param(
            INCOME,
            "income-plans",
            2,
            "0,02",
            id="income_tab_price_converted_in_template",
        ),
        pytest.param(
            EXPENSE,
            "everyday-expense-plans",
            2,
            "0,02",
            id="expense_tab_price_converted_in_template",
        ),
        pytest.param(
            SAVING,
            "saving-plans",
            2,
            "0,02",
            id="saving_tab_price_converted_in_template",
        ),
        pytest.param(
            NECESSARY,
            "necessary-plans",
            5,
            "0,05",
            id="necessary_tab_price_converted_in_template",
        ),
        pytest.param(
            DAY, "day-plans", 5, "0,05", id="day_tab_price_converted_in_template"
        ),
    ],
)
def test_plan_tab_price_converted_in_template(client_logged, kind, panel, price, text):
    owned = kind.owner()
    for month in range(1, 13):
        kind.factory(month=month, price=price, **owned)

    content = client_logged.get(reverse(kind.tab)).content.decode()
    assert len(_month_cells(_panel(content, panel), text)) == 12


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="incomes_delete"),
        pytest.param(EXPENSE, id="expenses_delete"),
        pytest.param(SAVING, id="saving_delete"),
        pytest.param(DAY, id="day_delete"),
        pytest.param(NECESSARY, id="necessary_delete"),
    ],
)
def test_plan_delete(client_logged, kind):
    owned = kind.owner()
    obj = kind.factory(year=1999, month=1, **owned)
    kind.factory(year=1999, month=2, **owned)
    kind.factory(year=2026, month=2, **owned)

    assert kind.model.objects.all().count() == 3

    url = reverse(kind.delete, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    client_logged.post(url, follow=True)

    assert kind.model.objects.all().count() == 1
    assert kind.model.objects.first().year == 2026


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="incomes_delete_returns_htmx_response"),
        pytest.param(EXPENSE, id="expenses_delete_returns_htmx_response"),
        pytest.param(SAVING, id="saving_delete_returns_htmx_response"),
        pytest.param(DAY, id="day_delete_returns_htmx_response"),
        pytest.param(NECESSARY, id="necessary_delete_returns_htmx_response"),
    ],
)
def test_plan_delete_returns_htmx_response(client_logged, kind):
    obj = kind.factory(year=1999, month=1, **kind.owner())

    url = reverse(kind.delete, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    response = client_logged.post(url)

    assert kind.model.objects.count() == 0
    assert response.status_code == 204
    _assert_reload_triggered(response)


@pytest.mark.parametrize(
    "kind, message",
    [
        pytest.param(
            INCOME,
            "1999 metai su 'Income Type'  jau turi tikslą.",
            id="income_new_prevents_duplicate_category_in_same_year",
        ),
        pytest.param(
            EXPENSE,
            "1999 metai su 'Expense Type'  jau turi tikslą.",
            id="expense_new_prevents_duplicate_category_in_same_year",
        ),
        pytest.param(
            SAVING,
            "1999 metai su 'Saving Type'  jau turi tikslą.",
            id="saving_new_prevents_duplicate_category_in_same_year",
        ),
    ],
)
def test_plan_new_prevents_duplicate_category_in_same_year(
    client_logged, kind, message
):
    owned = kind.owner()
    kind.factory(year=1999, month=1, **owned)

    data = {"year": "1999", "january": 9.99, **_form_values(owned)}

    content = client_logged.post(reverse(kind.new), data).content.decode()

    assert escape(message) in content


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(INCOME, id="incomes_delete_load_form"),
        pytest.param(EXPENSE, id="expenses_delete_load_form"),
        pytest.param(SAVING, id="saving_delete_load_form"),
        pytest.param(DAY, id="day_delete_load_form"),
        pytest.param(NECESSARY, id="necessary_delete_load_form"),
    ],
)
def test_plan_delete_load_form(client_logged, kind):
    obj = kind.factory(year=1999)

    url = reverse(kind.delete, kwargs={"year": 1999, **kind.own_kwargs(obj)})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert form_posts_to(actual, "delete-form", url)
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


# Plans of another journal
def _other_journal_plan(kind, second_user):
    journal = second_user.journal
    return kind.factory(
        journal=journal, month=1, price=666, **kind.owner(journal=journal)
    )


def _other_journal_url(kind, name, second_user):
    obj = _other_journal_plan(kind, second_user)
    return reverse(name, kwargs={"year": 1999, **kind.own_kwargs(obj)})


ALL_KINDS = [
    pytest.param(INCOME, id="income"),
    pytest.param(EXPENSE, id="expense"),
    pytest.param(SAVING, id="saving"),
    pytest.param(DAY, id="day"),
    pytest.param(NECESSARY, id="necessary"),
]


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_plan_update_not_load_other_journal(client_logged, second_user, kind):
    url = _other_journal_url(kind, kind.update, second_user)

    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_plan_delete_other_journal_get_form(client_logged, second_user, kind):
    url = _other_journal_url(kind, kind.delete, second_user)

    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_plan_delete_other_journal_post_form(client_logged, second_user, kind):
    url = _other_journal_url(kind, kind.delete, second_user)

    response = client_logged.post(url)

    assert response.status_code == 404
    assert kind.model.objects.all().count() == 1


# DayPlan
@time_machine.travel("2026-09-15")
def test_day_tab_cards_read_the_current_month_in_the_selected_plan_year(
    client_logged, main_user
):
    main_user.year = 2027
    main_user.save()
    DayPlanFactory(year=2026, month=9, price=9900)
    DayPlanFactory(year=2027, month=8, price=5000)
    DayPlanFactory(year=2027, month=9, price=3000)
    for month in range(1, 13):
        IncomePlanFactory(year=2027, month=month, price=90_000)
    SavingPlanFactory(year=2027, month=9, price=30_000)

    content = client_logged.get(reverse("plans:tab_day")).content.decode()

    assert _card_figure(content, "Suma dienai šį mėnesį") == "20,00"
    assert _card_figure(content, "Dienos planas šį mėnesį") == "30,00"


def _card_figure(content, title):
    card = content.split(f'<div class="trend-card__label">{title}</div>')[1]
    return re.search(r'trend-card__figure" title="[^"]*">([^<]*)<', card).group(1)


def test_day_new_duplicates_not_allowed(client_logged):
    DayPlanFactory(year=1999, month=12, price=100)

    data = {"year": "1999", "january": 0.05}

    content = client_logged.post(reverse("plans:day_new"), data).content.decode()

    assert "1999 metai jau turi tikslą." in content


def test_day_update(client_logged):
    obj = DayPlanFactory(year=1999, month=1, price=5)

    data = {"year": "1999", "january": 0.01}
    url = reverse("plans:day_update", kwargs={"year": 1999})

    client_logged.post(url, data, follow=True)
    actual = DayPlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 1


def test_day_tab_calculations_shows_the_chain_labels_not_the_old_numbering(
    client_logged,
):
    url = reverse("plans:tab_day")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")
    actual = _between(content, "calculations-spend")
    labels = re.findall(
        r'<h2 class="panel__title">([^<]*)<|<td class="text-left">([^<]*)<', actual
    )

    assert ["".join(label) for label in labels] == [
        "Kiek galiu išleisti per dieną",
        "Pajamos",
        "Būtinos išlaidos ir taupymas",
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Taupymas",
        "Laisvi pinigai",
        "Suma dienai",
        "Dienos planas",
        "Likutis",
        "Patikra: ar telpa išlaidų planai",
        "Kasdienės išlaidos pagal planą",
        "Visos išlaidos",
        "Lieka po išlaidų planų",
    ]
    assert "1. Pajamos" not in actual
    assert "iš lentelių viršuje" not in actual
    assert '<h2 class="panel__title">Skaičiavimai</h2>' not in content
    assert ">Pajamos − visos išlaidos<" not in content


def test_day_tab_calculations_renders_two_panels_each_with_its_own_header(
    client_logged,
):
    url = reverse("plans:tab_day")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    spend = _between(content, "calculations-spend", "calculations-check")
    check = _between(content, "calculations-check")

    assert spend.count("<thead") == 1
    assert check.count("<thead") == 1


def _first_month_cell(content, label):
    row = rf'<td class="text-left">{label}(?:<span[^>]*>.*?</span>)?</td>\s*'
    return re.search(row + r"<td[^>]*>([^<]*)</td>", content).group(1)


def test_day_tab_calculations_breakdown_reads_the_plans(client_logged):
    ExpensePlanFactory(
        price=10_000, expense_type=ExpenseTypeFactory(title="N", necessary=True)
    )
    NecessaryPlanFactory(price=5_000)
    SavingPlanFactory(price=3_000)

    content = client_logged.get(reverse("plans:tab_day")).content.decode()

    assert _first_month_cell(content, "Būtinos išlaidos") == "100,00"
    assert _first_month_cell(content, "Papildomos būtinos išlaidos") == "50,00"
    assert _first_month_cell(content, "Taupymas") == "30,00"


def test_day_tab_calculations_marks_the_day_plan_cell_above_the_sum_per_day(
    client_logged,
):
    DayPlanFactory(month=1, price=5_000)

    response = client_logged.get(reverse("plans:tab_day"))
    content = response.content.decode("utf-8")
    actual = _between(content, "calculations-spend", "calculations-check")

    assert actual.count("plans-table__over") == 1


# NecessaryPlan
def test_necessary_new(client_logged, main_user):
    e = ExpenseTypeFactory()
    data = {"year": "1999", "title": "ABCD", "january": 0.66, "expense_type": e.pk}

    url = reverse("plans:necessary_new")
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.title == "ABCD"
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 66


def test_necessary_new_duplicates_not_allowed(client_logged):
    e = ExpenseTypeFactory()
    NecessaryPlanFactory(year=1999, title="XXX", expense_type=e)
    data = {"year": "1999", "title": "XXX", "january": 0.66, "expense_type": e.pk}

    content = client_logged.post(reverse("plans:necessary_new"), data).content.decode()

    assert escape("1999 metai su 'Expense Type ir XXX'  jau turi tikslą.") in content


def test_necessary_new_not_load_other_journal(client_logged, second_user):
    ExpenseTypeFactory(title="AAA")
    ExpenseTypeFactory(journal=second_user.journal, title="XXX")

    url = reverse("plans:necessary_new")
    content = client_logged.get(url).content.decode("utf-8")

    options = re.findall(
        r'<option value="(\d*)"[^>]*>([^<]*)</option>', _select(content, "expense_type")
    )
    assert [title for pk, title in options if pk] == ["AAA"]


def test_necessary_update(client_logged):
    obj = NecessaryPlanFactory(year=1999, title="ABCD", month=1, price=666)

    data = {"year": "1999", "title": "X", "january": 0.01}
    url = reverse(
        "plans:necessary_update",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 1


# Copy Plans
def test_copy_load_form(client_logged):
    url = reverse("plans:copy")

    content = client_logged.get(url).content.decode()

    assert form_posts_to(content, "generic-form", url)
    for name in (
        "year_from",
        "year_to",
        "income",
        "expense",
        "saving",
        "day",
        "necessary",
    ):
        assert f'name="{name}"' in content


def test_copy_success(main_user, client_logged):
    IncomePlanFactory(year=1999)
    data = {"year_from": "1999", "year_to": "2000", "income": True}

    url = reverse("plans:copy")
    client_logged.post(url, data, follow=True)

    actual = IncomePlanModelService(main_user).year(2000)

    assert actual[0].year == 2000


def test_copy_fails(client_logged):
    data = {"year_from": "1999", "year_to": "2000", "income": True}

    content = client_logged.post(reverse("plans:copy"), data).content.decode()

    assert "Nėra ką kopijuoti." in content
    assert not IncomePlan.objects.exists()


def test_copy_year_to_same_as_user_year(main_user, client_logged):
    IncomePlanFactory(year=1999)

    main_user.year = 2000
    main_user.save()

    data = {"year_from": "1999", "year_to": "2000", "income": True}

    url = reverse("plans:copy")
    response = client_logged.post(url, data)

    _assert_reload_triggered(response)


# Query counts
def _income_plans(numbers):
    for i in numbers:
        IncomePlanFactory(income_type=IncomeTypeFactory(title=f"I{i}"))


def _expense_plans(numbers):
    for i in numbers:
        ExpensePlanFactory(expense_type=ExpenseTypeFactory(title=f"E{i}"))


def _necessary_plans(numbers):
    for i in numbers:
        NecessaryPlanFactory(expense_type=ExpenseTypeFactory(title=f"N{i}"))


def _saving_plans(numbers):
    for i in numbers:
        SavingPlanFactory(saving_type=SavingTypeFactory(title=f"S{i}"))


def _day_plans(numbers):
    for i in numbers:
        DayPlanFactory(month=i + 1)


def _plans_of_every_type(numbers):
    _income_plans(numbers)
    _expense_plans(numbers)
    _necessary_plans(numbers)
    _saving_plans(numbers)


@pytest.mark.parametrize(
    "tab_name, build",
    [
        pytest.param("incomes", _income_plans, id="incomes_tab_plans"),
        pytest.param("expenses", _expense_plans, id="expenses_tab_expense_plans"),
        pytest.param("expenses", _necessary_plans, id="expenses_tab_necessary_plans"),
        pytest.param("savings", _saving_plans, id="savings_tab_plans"),
        pytest.param("day", _plans_of_every_type, id="day_tab_plan_types"),
        pytest.param("day", _day_plans, id="day_tab_plans"),
    ],
)
def test_tab_query_count_does_not_grow_with_the_plans(client_logged, tab_name, build):
    url = TABS[tab_name].url

    def load_tab():
        client_logged.get(url, headers={"HX-Request": "true"})

    build(range(2))
    two = count_queries(load_tab)

    build(range(2, 6))
    six = count_queries(load_tab)

    assert six == two


def test_expenses_tab_reads_no_income_saving_or_day_plans(client_logged):
    tab = TABS["expenses"]
    ExpensePlanFactory()
    NecessaryPlanFactory()

    with CaptureQueriesContext(connection) as queries:
        client_logged.get(tab.url, headers={"HX-Request": "true"})

    sql = " ".join(query["sql"] for query in queries.captured_queries)
    for table in ("plans_incomeplan", "plans_savingplan", "plans_dayplan"):
        assert table not in sql


PLAN_DATA = (views.TabViewMixin, "plan_data")
DAY_SUM = (views, "PlanCalculateDaySum")


@pytest.mark.parametrize(
    "call, patched",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabIncomes).get_context_data(),
            [PLAN_DATA],
            id="tab_incomes",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabExpenses).get_context_data(),
            [PLAN_DATA],
            id="tab_expenses",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabSavings).get_context_data(),
            [PLAN_DATA],
            id="tab_savings",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabDay).get_context_data(),
            [PLAN_DATA, DAY_SUM],
            id="tab_day",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabDay).plan_data(), [], id="plan_data"
        ),
        pytest.param(
            lambda rf, u: forms.DayPlanForm(user=u, today=date(1999, 1, 1)),
            [],
            id="plan_form",
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, mocker, call, patched):
    main_user.year = None
    for owner, attr in patched:
        mocker.patch.object(owner, attr)

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)
