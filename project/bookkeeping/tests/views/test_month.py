import re
from datetime import date
from pathlib import Path

import pytest
from django.urls import reverse

from ....core.tests.utils import clean_content
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....plans.tests.factories import DayPlanFactory

pytestmark = pytest.mark.django_db

EXPANDED_DAY_SNAPSHOT = Path(__file__).parent / "snapshots" / "expanded_day.html"


def test_view_month_import_button_after_expenses_button(client_logged):
    url = reverse("bookkeeping:month")
    response = client_logged.get(url)
    text = response.content.decode()

    expenses_url = reverse("expenses:new")
    import_url = reverse("expenses:import")
    buttons = re.search(r'<div id="month-add-buttons"[^>]*>(.*?)</div>', text, re.S)[1]
    expenses = re.search(rf'<button type="button"[^>]*hx-get="{expenses_url}"', buttons)
    receipt = re.search(
        rf'<a href="{import_url}" class="button-outline-success import-receipt">'
        "Importuoti čekį</a>",
        buttons,
    )

    assert expenses
    assert receipt
    assert expenses.start() < receipt.start()


def _january_page(client):
    return client.get(reverse("bookkeeping:month"), {"month": 1}).content.decode()


def test_view_month_day_over_budget_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    text = _january_page(client_logged)

    assert re.search(r'<td data-sign="loss" class="day-warning[ "]', text)
    assert "table-danger" not in text


def test_view_month_day_cells_within_budget_carry_no_sign(client_logged):
    DayPlanFactory(year=1999, month=1, price=1000000)
    ExpenseFactory(date=date(1999, 1, 1), price=1)

    text = _january_page(client_logged)
    cells = re.findall(r'<td([^>]*)class="day-(?:warning|negative)[ "]', text)

    assert cells
    assert all("data-sign" not in attrs for attrs in cells)


def test_view_month_negative_cumulative_balance_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    text = _january_page(client_logged)

    assert re.search(r'<td data-sign="loss" class="day-negative[ "]', text)


def test_view_month_plan_table_rows_carry_their_sign(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    text = _january_page(client_logged)
    signs = re.findall(r'<tr data-sign="(\w*)">', text)

    assert signs[:3] == ["gain", "loss", "gain"]


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 1),
        ("x", 12),
    ],
)
def test_view_month_saves_the_month_it_shows(month, expect, main_user, client_logged):
    url = reverse("bookkeeping:month")
    client_logged.get(url, {"month": month})

    main_user.refresh_from_db()
    assert main_user.month == expect


def test_view_month_requested_by_htmx_returns_the_content_alone(client_logged):
    url = reverse("bookkeeping:month")
    content = client_logged.get(url, headers={"HX-Request": "true"}).content.decode()

    assert '<main class="month-grid"' in content
    assert '<nav id="main-nav">' not in content
    assert "js/modal.js" not in content
    assert 'id="month-page"' not in content


@pytest.mark.parametrize(
    "headers",
    [{}, {"HX-Request": "true", "HX-History-Restore-Request": "true"}],
    ids=["plain", "history-restore"],
)
def test_view_month_renders_the_whole_page(client_logged, headers):
    url = reverse("bookkeeping:month")
    content = client_logged.get(url, headers=headers).content.decode()

    assert '<nav id="main-nav">' in content
    assert '<div id="month-page">' in content


@pytest.mark.parametrize(
    "swap",
    [
        'hx-get="/month/?month=1" hx-target="#month-page"',
        'hx-get="/month/" hx-target="#month-page" hx-trigger="reload from:body"',
    ],
    ids=["month-button", "reload"],
)
def test_view_month_swaps_aim_at_its_content(client_logged, swap):
    url = reverse("bookkeeping:month")
    content = client_logged.get(url, headers={"HX-Request": "true"}).content.decode()

    assert swap in content
    assert 'hx-target="body"' not in content


@pytest.mark.parametrize("dt", ["xx", "1970-13-01", "1970-12-32"])
def test_view_expand_day_expenses_wrong_dates(dt, client_logged):
    response = client_logged.get(f"/month/{dt}/")

    assert response.status_code == 404


def test_an_empty_expanded_day_keeps_its_reloading_notice(client_logged):
    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": date(1999, 1, 1)})
    actual = clean_content(client_logged.get(url).content.decode("utf-8"))

    assert (
        f'<div class="alert alert-warning" hx-trigger="reload from:body" hx-get="{url}"'
        ' hx-target="#data" hx-indicator="#indicator">1999-01-01 dieną įrašų nėra</div>'
    ) in actual


def test_expanded_day_expenses_markup_unchanged(client_logged):
    # explicit pks: they reach the row colour and the urls, and a factory's varies
    food = ExpenseTypeFactory(pk=1, title="Food")
    drinks = ExpenseTypeFactory(pk=2, title="Drinks")
    ExpenseFactory(
        pk=1,
        expense_type=food,
        expense_name=ExpenseNameFactory(title="Bread", parent=food),
        exception=True,
    )
    ExpenseFactory(
        pk=2,
        expense_type=food,
        expense_name=ExpenseNameFactory(title="Milk", parent=food),
        attachment="1/1/1999.01_milk.jpg",
    )
    ExpenseFactory(
        pk=3,
        expense_type=drinks,
        expense_name=ExpenseNameFactory(title="Beer", parent=drinks),
        attachment="1/2/1999.01_beer.pdf",
    )

    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": date(1999, 1, 1)})
    actual = client_logged.get(url).content.decode("utf-8")
    expected = EXPANDED_DAY_SNAPSHOT.read_text(encoding="utf-8")

    assert _without_whitespace(actual) == _without_whitespace(expected)


def _without_whitespace(html):
    return re.sub(r"\s+", " ", re.sub(r"\s*([<>])\s*", r"\1", html))


@pytest.mark.parametrize(
    "chart_type, script",
    [
        pytest.param("targets", "chart_month_targets.js", id="targets"),
        pytest.param("expenses", "chart_month_expenses.js", id="expenses"),
        pytest.param("xxx", "chart_month_expenses.js", id="unknown_is_expenses"),
    ],
)
def test_view_month_chart_loads_its_script(client_logged, chart_type, script):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": chart_type})
    content = client_logged.get(url).content.decode("utf-8")

    assert re.search(rf'<script\b[^>]*\bsrc="/static/js/{script}"></script>', content)


def test_view_month_chart_sends_anonymous_to_login(client):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": "xxx"})
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('users:login')}?next={url}"
