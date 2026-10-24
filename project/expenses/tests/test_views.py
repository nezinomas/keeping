import json
import re
from datetime import date
from unittest.mock import patch

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.lib.utils import get_action_buttons_html
from ...core.tests.utils import (
    clean_content,
    quick_add_pills,
    stat_card_tooltips,
    stat_cards,
    view_for,
)
from .. import models
from ..forms import ExpenseNameChoicesMixin
from ..forms_import import ReviewLineForm
from ..views import expenses as expense_views
from ..views import expenses_import
from ..views.expenses import Lists, LoadExpenseName
from ..views.expenses_type import TabTypes
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def type_with_two_names():
    expense_type = ExpenseTypeFactory()
    ExpenseNameFactory(title="F", parent=expense_type)
    ExpenseNameFactory(title="S", parent=expense_type, valid_for=1999)
    return expense_type


def _active_tab(name):
    return rf'id="tab-{name}"\s+class="tab active"'


def _open_month(month):
    # each pattern names the element that carries the url: the filter line lists
    # every month, the Reset button and #data share one url
    return [
        rf'id="data"[^>]*hx-get="/expenses/list/{month}/"',
        rf'class="button-secondary"\s+hx-get="/expenses/list/{month}/"',
        rf'aria-current="true" hx-get="/expenses/data/{month}/" hx-push-url="true"',
        rf'<div hx-get="/expenses/data/{month}/" hx-target="#tab_content"',
    ]


# the travel's month, which the subnav's Duomenys opens from any month's page
SUBNAV_DUOMENYS_AT_TODAY = r'id="tab-data"[^>]*hx-get="/expenses/data/2/"'


@pytest.mark.parametrize(
    "url_name, kwargs, query, expected",
    [
        pytest.param("expenses:index", {}, {}, [_active_tab("index")], id="overview"),
        pytest.param(
            "expenses:tab_data",
            {"month": "2"},
            {},
            [_active_tab("data"), *_open_month(2)],
            id="data_this_month",
        ),
        pytest.param(
            "expenses:tab_data",
            {"month": "3"},
            {},
            [_active_tab("data"), *_open_month(3), SUBNAV_DUOMENYS_AT_TODAY],
            id="nav_month",
        ),
        pytest.param(
            "expenses:tab_data",
            {"month": "3"},
            {"month": "5"},
            [_active_tab("data"), *_open_month(3)],
            id="the_path_wins_over_a_query",
        ),
        pytest.param(
            "expenses:tab_data",
            {"month": "all"},
            {},
            [_active_tab("data"), *_open_month("all"), SUBNAV_DUOMENYS_AT_TODAY],
            id="all",
        ),
        pytest.param(
            "expenses:tab_data",
            {"month": "13"},
            {},
            [_active_tab("data"), *_open_month(2)],
            id="13_falls_back",
        ),
    ],
)
@time_machine.travel("1999-02-08")
def test_the_page_opens_the_tab_and_month_its_url_names(
    client_logged, url_name, kwargs, query, expected
):
    url = reverse(url_name, kwargs=kwargs)
    content = client_logged.get(url, query).content.decode()

    for pattern in expected:
        assert re.search(pattern, content)


@pytest.mark.parametrize("path", ["/expenses/data/", "/expenses/list/", "/expenses/3/"])
def test_duomenys_and_its_list_have_no_route_without_a_month(client_logged, path):
    assert client_logged.get(path).status_code == 404


def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged):
    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert '<div class="tabs" role="tablist"' in content


def test_quick_add_offers_its_pills(client_logged):
    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert quick_add_pills(content) == [
        ("a", "", 'href="/expenses/import/"', "Importuoti čekį"),
        ("button", "", 'hx-get="/expenses/new/"', "Pridėti išlaidas"),
        ("button", "types", 'hx-get="/expenses/type/new/"', "Pridėti išlaidų rūšį"),
        (
            "button",
            "types",
            'hx-get="/expenses/name/new/"',
            "Pridėti išlaidų pavadinimą",
        ),
    ]


def test_a_tab_url_requested_by_htmx_returns_the_fragment_alone(client_logged):
    content = client_logged.get(
        reverse("expenses:tab_index"), headers={"HX-Request": "true"}
    ).content.decode()

    assert "<title>Išlaidos | Apžvalga</title>" in content
    assert 'role="tablist"' not in content
    assert 'class="quick-add' not in content


def _tab_queries(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url, headers={"HX-Request": "true"})
    return len(queries)


def _expense_under_its_own_name(i):
    expense_type = ExpenseTypeFactory(title=f"T{i}")
    name = ExpenseNameFactory(title=f"N{i}", parent=expense_type)
    ExpenseFactory(expense_type=expense_type, expense_name=name)


@pytest.mark.parametrize(
    "url_name, kwargs",
    [
        pytest.param("expenses:tab_index", {}, id="expenses:tab_index"),
        pytest.param("expenses:tab_data", {"month": "all"}, id="expenses:tab_data"),
        pytest.param("expenses:tab_types", {}, id="expenses:tab_types"),
    ],
)
def test_tab_query_count_does_not_grow_with_the_expenses(
    client_logged, url_name, kwargs
):
    url = reverse(url_name, kwargs=kwargs)
    for i in range(2):
        _expense_under_its_own_name(i)
    two = _tab_queries(client_logged, url)

    for i in range(2, 6):
        _expense_under_its_own_name(i)
    six = _tab_queries(client_logged, url)

    assert six == two


def _spend(name, cents, when):
    ExpenseFactory(date=when, price=cents, expense_type=name.parent, expense_name=name)


def test_types_tab_lists_each_type_with_its_names_beneath(client_logged):
    food = ExpenseTypeFactory(title="Maistas")
    milk = ExpenseNameFactory(title="Pienas", parent=food)
    bread = ExpenseNameFactory(title="Duona", parent=food)
    ExpenseNameFactory(title="Sūris", parent=food)
    soap = ExpenseNameFactory(
        title="Muilas", parent=ExpenseTypeFactory(title="Buitinės")
    )
    ExpenseTypeFactory(title="Tuščia")
    _spend(milk, 60_000, date(1999, 2, 5))
    _spend(milk, 20_000, date(1998, 1, 1))
    _spend(bread, 30_000, date(1999, 3, 7))
    _spend(soap, 10_000, date(1999, 4, 1))

    content = client_logged.get(reverse("expenses:tab_types")).content.decode()

    def cells(*values):
        return r"\s*".join(f"<td>{value}</td>" for value in values)

    def name_cells(this_year, last_year, share, last_expense):
        share_cell = f'<td class="main__share">{share}</td>'
        return r"\s*".join(
            (cells(this_year, last_year), share_cell, cells(last_expense))
        )

    rows = [
        r'<tbody>\s*<tr class="main__group"[^>]*>\s*'
        r'<td class="text-left">Buitinės</td>\s*'
        + cells(100, "–", "10%", "1999-04-01"),
        r'<tr[^>]*>\s*<td class="text-left main__child">Muilas</td>\s*'
        + name_cells(100, "–", "100%", "1999-04-01"),
        r'</tbody>\s*<tbody>\s*<tr class="main__group table-group-divider"[^>]*>\s*'
        r'<td class="text-left">Maistas</td>\s*' + cells(900, 200, "90%", "1999-03-07"),
        r'<tr[^>]*>\s*<td class="text-left main__child">Duona</td>\s*'
        + name_cells(300, "–", "33%", "1999-03-07"),
        r'<tr[^>]*>\s*<td class="text-left main__child">Pienas</td>\s*'
        + name_cells(600, 200, "67%", "1999-02-05"),
        r'<tr[^>]*>\s*<td class="text-left main__child">Sūris</td>\s*'
        + name_cells("–", "–", "–", "–"),
        r'</tbody>\s*<tbody>\s*<tr class="main__group table-group-divider"[^>]*>\s*'
        r'<td class="text-left">Tuščia</td>\s*' + cells("–", "–", "–", "–"),
        r'</tbody>\s*<tfoot>\s*<tr class="main__total">\s*'
        r'<td class="text-left">Viso</td>\s*' + cells("1.000", 200, "100%"),
    ]
    assert re.search(r"[\s\S]*?".join(rows), content)


@pytest.mark.parametrize(
    "necessary, title_cell",
    [
        (True, 'Būstas <span class="main__mark">būtinos</span></td>'),
        (False, '<td class="text-left">Būstas</td>'),
    ],
    ids=["necessary_reads_its_caption", "other_has_none"],
)
def test_types_tab_captions_a_necessary_type(client_logged, necessary, title_cell):
    ExpenseTypeFactory(title="Būstas", necessary=necessary)

    content = client_logged.get(reverse("expenses:tab_types")).content.decode()

    assert title_cell in content


def test_types_tab_of_a_past_year_shows_its_own_last_expense(client_logged):
    milk = ExpenseNameFactory(title="Pienas", parent=ExpenseTypeFactory(title="M"))
    _spend(milk, 100, date(1999, 5, 5))
    _spend(milk, 100, date(2000, 2, 2))

    content = client_logged.get(reverse("expenses:tab_types")).content.decode()

    assert "<td>1999-05-05</td>" in content
    assert "2000-02-02" not in content


def test_types_tab_lists_a_name_limited_to_another_year_with_its_year(client_logged):
    food = ExpenseTypeFactory(title="Maistas")
    ExpenseNameFactory(title="Senas", parent=food, valid_for=1998)
    ExpenseNameFactory(title="Šių metų", parent=food, valid_for=1999)

    content = client_logged.get(reverse("expenses:tab_types")).content.decode()

    assert 'main__child">Šių metų <span class="main__year">1999</span></td>' in content
    assert 'main__child">Senas <span class="main__year">1998</span></td>' in content
    assert 'class="filter-line"' not in content


@pytest.mark.parametrize("order", ["share", "title"])
def test_types_tab_sort_links_and_reload_carry_only_the_order(client_logged, order):
    query = {"order": order}

    content = client_logged.get(reverse("expenses:tab_types"), query).content.decode()

    # pushed, so a reload keeps the sort
    assert '<thead class="sortable-header-row" hx-push-url:inherited="true">' in content
    for key, label in (
        ("title", "Rūšis / pavadinimas"),
        ("this_year", "Šiemet"),
        ("last_year", "Pernai"),
        ("share", "Dalis"),
        ("last_expense", "Paskutinį kartą"),
    ):
        drawn = (
            f'<a role="button" hx-get="/expenses/types/?order={key}"'
            f' hx-target="#tab_content">{label}</a>'
        )
        if key == order:
            drawn = f"<span>{label}</span>"
        assert drawn in content
    assert re.search(r'<th class="text-left">\s*<(span|a [^>]*)>Rūšis', content)
    # a save reloads the sort shown
    reload = f'<div hx-get="/expenses/types/?order={order}" hx-target="#tab_content"'
    assert reload in content


def test_types_tab_edits_each_type_and_name_from_its_row(client_logged):
    food = ExpenseTypeFactory(title="Maistas")
    milk = ExpenseNameFactory(title="Pienas", parent=food)
    type_link = reverse("expenses:type_update", kwargs={"pk": food.pk})
    name_link = reverse("expenses:name_update", kwargs={"pk": milk.pk})

    content = client_logged.get(reverse("expenses:tab_types")).content.decode()

    for row, link in (('<tr class="main__group"', type_link), ("<tr", name_link)):
        dblclick = f'hx-get="{link}" hx-trigger="dblclick" hx-target="#mainModal">'
        assert f"{row} {dblclick}" in content
        assert re.search(rf'<a role="button" hx-get="{link}"[^>]*class="edit"', content)


def _type_update_url():
    return reverse("expenses:type_update", kwargs={"pk": ExpenseTypeFactory().pk})


def _name_update_url():
    return reverse("expenses:name_update", kwargs={"pk": ExpenseNameFactory().pk})


@pytest.mark.parametrize(
    "url_of, with_parent",
    [
        pytest.param(lambda: reverse("expenses:type_new"), False, id="type_new"),
        pytest.param(_type_update_url, False, id="type"),
        pytest.param(lambda: reverse("expenses:name_new"), True, id="name_new"),
        pytest.param(_name_update_url, True, id="name"),
    ],
)
def test_type_and_name_forms_reload_the_open_tab(client_logged, url_of, with_parent):
    data = {"title": "TTT"}
    if with_parent:
        data["parent"] = ExpenseTypeFactory(title="P").pk

    response = client_logged.post(url_of(), data, headers={"HX-Request": "true"})

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


@time_machine.travel("1999-09-15")
def test_overview_states_a_running_year_to_its_boundary(client_logged):
    food = ExpenseTypeFactory(title="Maistas")
    ExpenseFactory(date=date(1999, 2, 5), price=90_000, expense_type=food)
    ExpenseFactory(date=date(1999, 11, 5), price=60_000, expense_type=food)
    ExpenseFactory(date=date(1998, 1, 5), price=80_000, expense_type=food)
    ExpenseFactory(date=date(1998, 12, 5), price=5_000, expense_type=food)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert stat_cards(content) == [
        ("Šiais metais", "900", "Pernai 800"),
        ("Per mėnesį", "100", "9 mėnesiai"),
        ("Didžiausia rūšis", "Maistas", "100% metų sumos"),
    ]
    assert stat_card_tooltips(content) == [
        "Metų suma, padalinta iš prabėgusių mėnesių",
        "Didžiausią šių metų dalį sudaranti išlaidų rūšis",
    ]


def test_overview_of_a_past_year_reads_the_whole_year(client_logged):
    ExpenseFactory(date=date(1999, 3, 5), price=60_000)
    ExpenseFactory(date=date(1998, 12, 5), price=5_000)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert stat_cards(content) == [
        ("Šiais metais", "600", "Pernai 50"),
        ("Per mėnesį", "50", "12 mėnesių"),
        ("Didžiausia rūšis", "Expense Type", "100% metų sumos"),
    ]


def test_overview_of_an_empty_year_is_three_empty_cards(client_logged):
    ExpenseFactory(date=date(1998, 3, 5))

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert content.count("trend-card__value--empty") == 3


@time_machine.travel("1999-09-15")
def test_overview_charts_the_year_against_last_year_to_the_same_day(client_logged):
    ExpenseFactory(date=date(1999, 2, 5), price=90_000)
    ExpenseFactory(date=date(1998, 9, 10), price=80_000)
    ExpenseFactory(date=date(1998, 9, 20), price=5_000)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()
    chart = json.loads(
        re.search(r'id="chart-months-data"[^>]*>(.*?)</script>', content)[1]
    )
    data = {series["name"]: series["data"] for series in chart["series"]}

    assert data["1999"] == [0.0, 900.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert data["1998"][8] == 800.0
    assert re.search(
        r'<h2 class="panel__title">Išlaidos per mėnesį</h2>\s*'
        r'<div id="chart-months-container">',
        content,
    )


def test_the_navbar_opens_duomenys_at_each_month_and_all(client_logged):
    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert re.findall(r'href="(/expenses/data/[^"]*)"', content) == [
        *(f"/expenses/data/{month}/" for month in range(1, 13)),
        "/expenses/data/all/",
    ]


YEAR_DATES = [date(1998, 1, 1), date(1999, 1, 1), date(1999, 2, 1)]


@pytest.mark.parametrize(
    "today, dates, kwargs, query, expected",
    [
        pytest.param(
            "1999-02-08",
            [date(1999, 1, 1), date(1999, 2, 7)],
            {"month": "1"},
            {},
            [date(1999, 1, 1)],
            id="path_month",
        ),
        pytest.param(
            "1999-02-08",
            [date(1999, 1, 1), date(1999, 2, 7)],
            {"month": "1"},
            {"month": "2"},
            [date(1999, 1, 1)],
            id="the_path_wins_over_a_query",
        ),
        pytest.param(
            "1999-01-01",
            YEAR_DATES,
            {"month": "1"},
            {},
            [date(1999, 1, 1)],
            id="month_in_user_year",
        ),
        pytest.param(
            "1999-01-01",
            YEAR_DATES,
            {"month": "all"},
            {},
            [date(1999, 1, 1), date(1999, 2, 1)],
            id="all_is_the_year",
        ),
    ],
)
def test_expenses_list_filters_by_month(
    client_logged, today, dates, kwargs, query, expected
):
    for expense_date in dates:
        ExpenseFactory(date=expense_date)

    url = reverse("expenses:list", kwargs=kwargs)
    with time_machine.travel(today):
        content = client_logged.get(url, query).content.decode()

    listed = re.findall(r'<td class="text-left [\w-]+">(\d{4}-\d\d-\d\d)</td>', content)
    assert sorted(listed) == [day.isoformat() for day in expected]


@pytest.mark.parametrize(
    "month, expected",
    [
        pytest.param("1", "Mėnesį 1 įrašų nėra.", id="month"),
        pytest.param("all", "1999 metais įrašų nėra.", id="all"),
        pytest.param("13", "Mėnesį 2 įrašų nėra.", id="13_today"),
    ],
)
@time_machine.travel("1999-02-08")
def test_expenses_list_empty_notice(client_logged, month, expected):
    url = reverse("expenses:list", kwargs={"month": month})
    actual = client_logged.get(url).content.decode("utf-8")

    assert f'<div class="alert">{expected}</div>' in clean_content(actual)
    assert "<b>" not in actual
    assert "alert-warning" not in actual
    assert not re.search(r'hx-trigger="[^"]*reload from:body', actual)


def test_a_duomenys_row_has_no_type_colour_and_keeps_its_exception_mark(
    client_logged,
):
    # pk 1 is a type colorize.py paints, so a drawn colour would show here
    ExpenseFactory(expense_type=ExpenseTypeFactory(pk=1), exception=True)

    url = reverse("expenses:list", kwargs={"month": 1})
    content = client_logged.get(url).content.decode("utf-8")

    row = re.search(r'<tr hx-get=[^>]*class="([^"]*)"', content)[1]
    assert row.strip() == ""
    assert '<td class="text-left exception">1999-01-01</td>' in content
    assert not re.search(r'hx-trigger="[^"]*reload from:body', content)


def test_lists_renders_row_buttons_equal_for_2_and_6_expenses(client_logged):
    url = reverse("expenses:list", kwargs={"month": 1})
    buttons = {"cotton/td_edit.html", "cotton/td_delete.html"}
    # the buttons render once per process (lru_cache): warm it, or the first
    # request alone renders them
    get_action_buttons_html()

    def button_renders():
        templates = client_logged.get(url).templates
        return sorted(t.name for t in templates if t.name in buttons)

    ExpenseFactory.create_batch(2)
    two = button_renders()
    ExpenseFactory.create_batch(4)
    six = button_renders()

    assert two == six


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/expenses/list/1/", id="list"),
        pytest.param("/expenses/load_expense_name/", id="load_expense_name"),
    ],
)
def test_anonymous_is_sent_to_login(client, url):
    # a view that serves anonymous crashes on its user: read that as a status, not an error
    client.raise_request_exception = False
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('users:login')}?next={url}"


@time_machine.travel("1974-08-08")
def test_expenses_load_new_form(main_user, client_logged):
    main_user.year = 3000
    main_user.save()

    url = reverse("expenses:new")

    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert '<input type="text" name="date" value="3000-08-08"' in actual
    assert "Įrašyti</button>" in actual
    assert "Įrašyti ir uždaryti</button>" in actual


def test_expenses_new_form_file_control_speaks_the_app_language(client_logged):
    url = reverse("expenses:new")

    text = client_logged.get(url).content.decode()

    assert '<span class="file-input__button">Pasirinkti failą</span>' in text
    assert 'data-empty="Failas nepasirinktas"' in text


def test_expenses_save(client_logged):
    account = AccountFactory()
    expense_type = ExpenseTypeFactory()
    expense_name = ExpenseNameFactory()

    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "quantity": 33,
        "account": account.pk,
        "expense_type": expense_type.pk,
        "expense_name": expense_name.pk,
    }

    url = reverse("expenses:new")
    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.last()
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(lambda expense: reverse("expenses:new"), id="new"),
        pytest.param(
            lambda expense: reverse("expenses:update", kwargs={"pk": expense.pk}),
            id="update",
        ),
    ],
)
def test_a_save_without_htmx_lands_on_duomenys_at_the_saved_month(client_logged, url):
    expense = ExpenseFactory(date=date(1999, 1, 1))
    data = {
        "date": "1999-05-03",
        "price": 1,
        "quantity": 1,
        "account": expense.account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }

    response = client_logged.post(url(expense), data)

    assert response.status_code == 302
    assert response["Location"] == "/expenses/data/5/"


def _field_errors(content):
    return dict(
        re.findall(
            r'aria-describedby="id_(\w+)_error"(?:(?!aria-describedby=)[\s\S])*?'
            r'<div class="invalid-feedback">([^<]*)</div>',
            content,
        )
    )


def test_expenses_save_invalid_data(client_logged):
    data = {
        "date": "x",
        "price": "x",
        "quantity": 0,
        "account": "x",
        "expense_type": "x",
    }

    url = reverse("expenses:new")
    content = client_logged.post(url, data).content.decode()

    assert _field_errors(content) == {
        "date": "Įveskite tinkamą datą.",
        "account": "Pasirinkite tinkamą reikšmę. Parinkta reikšmė nėra galima.",
        "expense_type": "Pasirinkite tinkamą reikšmę. Parinkta reikšmė nėra galima.",
        "expense_name": "Šis laukas yra privalomas.",
        "quantity": "Įsitikinkite, kad reikšmė yra didesnė arba lygi 1.",
        "price": "Įveskite skaičių.",
    }
    assert not models.Expense.objects.exists()


def test_expenses_load_update_form(client_logged):
    expense = ExpenseFactory()

    url = reverse("expenses:update", kwargs={"pk": expense.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert "Atnaujinti ir uždaryti</button>" in actual


def test_expenses_load_update_form_field_values(client_logged):
    expense = ExpenseFactory(price=1)

    url = reverse("expenses:update", kwargs={"pk": expense.pk})
    form = client_logged.get(url).content.decode()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert f'<option value="{expense.account.pk}" selected>Account1</option>' in form
    assert (
        f'<option value="{expense.expense_type.pk}" selected>Expense Type</option>'
        in form
    )
    assert (
        f'<option value="{expense.expense_name.pk}" selected>Expense Name</option>'
        in form
    )
    assert '<input type="number" name="quantity" value="13"' in form
    assert '<input type="text" name="price" value="0.01"' in form
    assert re.search(r'<textarea name="remark"[^>]*>\s*Remark</textarea>', form)


@pytest.mark.parametrize(
    "created, price, posted_date, expected_price",
    [
        pytest.param({}, 150, "1999-12-31", 15_000, id="saves_posted_values"),
        pytest.param({}, 150, "2010-12-31", 15_000, id="to_another_year"),
        pytest.param(
            {"date": date(2000, 3, 3), "price": 477},
            4.89,
            "2000-03-04",
            489,
            id="float_price_is_whole_cents",
        ),
        pytest.param(
            {"date": date(1974, 12, 12)},
            0.01,
            "1998-12-12",
            1,
            id="past_record",
        ),
    ],
)
def test_expenses_update(client_logged, created, price, posted_date, expected_price):
    expense = ExpenseFactory(**created)
    new_type = ExpenseTypeFactory(title="XXX")
    new_name = ExpenseNameFactory(title="YYY", parent=new_type)

    data = {
        "price": price,
        "quantity": 33,
        "date": posted_date,
        "remark": "Pastaba",
        "account": expense.account.pk,
        "expense_type": new_type.pk,
        "expense_name": new_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == date.fromisoformat(posted_date)
    assert actual.price == expected_price
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "XXX"
    assert actual.expense_name.title == "YYY"
    assert actual.remark == "Pastaba"


def test_expenses_update_price_for_closed_account(client_logged):
    account = AccountFactory(title="XXX", closed=2000)
    expense = ExpenseFactory(account=account, date=date(1999, 1, 1))

    data = {
        "price": 150,
        "quantity": 33,
        "date": expense.date,
        "remark": "Pastaba",
        "account": account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == expense.date
    assert actual.price == 15_000
    assert actual.quantity == 33
    assert actual.account.title == account.title
    assert actual.expense_type.title == expense.expense_type.title
    assert actual.expense_name.title == expense.expense_name.title
    assert actual.remark == "Pastaba"


def test_expenses_update_with_closed_account_date_greater_than_closed_value(
    client_logged,
):
    account = AccountFactory(title="XXX", closed=2000)
    expense = ExpenseFactory(account=account, date=date(1999, 1, 1))

    data = {
        "price": 150,
        "quantity": 33,
        "date": "2023-1-1",
        "remark": "Pastaba",
        "account": account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    content = client_logged.post(url, data).content.decode()

    assert _field_errors(content) == {
        "date": "Data negali būti vėlesnė nei sąskaitos uždarymo data. "
        "Sąskaita buvo uždaryta 2000."
    }


def test_expenses_not_load_other_journal(client_logged, second_user):
    own_account = AccountFactory(title="a1")
    other_account = AccountFactory(journal=second_user.journal, title="a2")
    own_type = ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseFactory(expense_type=own_type, account=own_account)
    other_expense = ExpenseFactory(
        expense_type=other_type, account=other_account, price=666
    )

    url = reverse("expenses:update", kwargs={"pk": other_expense.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert other_type.title not in form
    assert str(other_expense.price) not in form


def test_expenses_data_search_form(client_logged):
    url = reverse("expenses:tab_data", kwargs={"month": "1"})
    response = client_logged.get(url).content.decode("utf-8")

    search = reverse("expenses:search")
    assert '<input type="search" name="search"' in response
    assert re.search(rf'id="search-form"\s+hx-get="{search}"', response)


@pytest.mark.parametrize(
    "price, expected",
    [
        pytest.param(7777, "77,77", id="converted"),
        pytest.param(100_000, "1.000,00", id="with_thousands"),
    ],
)
def test_expenses_list_price_converted(client_logged, price, expected):
    ExpenseFactory(price=price)

    url = reverse("expenses:list", kwargs={"month": 1})
    content = client_logged.get(url).content.decode("utf-8")

    assert re.findall(
        r'<tr hx-get=[^>]*>\s*<td class="text-left [\w-]+">([^<]*)</td>\s*'
        r'<td class="text-left">([^<]*)</td>\s*<td class="text-left">([^<]*)</td>\s*'
        r"<td>([^<]*)</td>\s*<td>([^<]*)</td>",
        content,
    ) == [("1999-01-01", "Expense Type", "Expense Name", "13", expected)]


def test_view_expenses_delete_load_form(client_logged):
    expense = ExpenseFactory()

    url = reverse("expenses:delete", kwargs={"pk": expense.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert re.search(
        rf'<form method="POST" id="delete-form"[^>]*hx-post="{url}"', actual
    )
    assert (
        "Ar tikrai norite ištrinti: "
        "<strong>1999-01-01/Expense Type/Expense Name</strong>?"
    ) in actual


def test_view_expenses_delete(client_logged):
    expense = ExpenseFactory()

    assert models.Expense.objects.all().count() == 1
    url = reverse("expenses:delete", kwargs={"pk": expense.pk})

    client_logged.post(url)

    assert models.Expense.objects.all().count() == 0


def test_expenses_delete_other_journal_get_form(client_logged, second_user):
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    other_expense = ExpenseFactory(
        expense_type=other_type,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expenses_delete_other_journal_post_form(client_logged, second_user):
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    other_expense = ExpenseFactory(
        expense_type=other_type,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
    client_logged.post(url)

    assert models.Expense.objects.all().count() == 1


def test_expense_type_not_load_other_journal(client_logged, second_user):
    ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("expenses:type_update", kwargs={"pk": other_type.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert other_type.title not in form


@pytest.mark.parametrize(
    "url_of",
    [
        pytest.param(lambda: reverse("expenses:new"), id="new"),
        pytest.param(
            lambda: reverse("expenses:update", kwargs={"pk": ExpenseFactory().pk}),
            id="update",
        ),
        pytest.param(lambda: reverse("expenses:type_new"), id="type_new"),
        pytest.param(lambda: reverse("expenses:name_new"), id="name_new"),
        pytest.param(_type_update_url, id="type_update"),
        pytest.param(_name_update_url, id="name_update"),
    ],
)
def test_each_form_posts_to_its_url(client_logged, url_of):
    url = url_of()
    actual = client_logged.get(url).content.decode("utf-8")

    assert re.search(rf'id="generic-form"[^>]*hx-post="{url}"', actual)


def test_expense_name_save_data(client_logged):
    url = reverse("expenses:name_new")
    expense_type = ExpenseTypeFactory()

    data = {"title": "TTT", "parent": expense_type.pk}

    client_logged.post(url, data)

    actual = models.ExpenseName.objects.get()
    assert actual.title == "TTT"
    assert actual.parent == expense_type


def test_expense_name_save_invalid_data(client_logged):
    data = {"title": "x", "parent": 0}

    url = reverse("expenses:name_new")

    content = client_logged.post(url, data).content.decode()

    assert _field_errors(content) == {
        "parent": "Pasirinkite tinkamą reikšmę. Parinkta reikšmė nėra galima.",
        "title": "Įsitikinkite, kad reikšmė sudaryta iš nemažiau kaip 3 ženklų "
        "(dabartinis ilgis 1).",
    }
    assert not models.ExpenseName.objects.exists()


def test_expense_name_load_for_form_for_update(client_logged):
    expense_name = ExpenseNameFactory(title="XXX")

    url = reverse("expenses:name_update", kwargs={"pk": expense_name.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="title" value="XXX"' in actual


def test_expense_name_update(client_logged):
    expense_name = ExpenseNameFactory()

    data = {"title": "TTT", "valid_for": 1999, "parent": expense_name.parent.pk}
    url = reverse("expenses:name_update", kwargs={"pk": expense_name.pk})

    client_logged.post(url, data)

    expense_name.refresh_from_db()
    assert expense_name.title == "TTT"
    assert expense_name.valid_for == 1999


def test_expense_name_not_load_other_journal(client_logged, second_user):
    own_type = ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseNameFactory(parent=own_type)
    other_name = ExpenseNameFactory(parent=other_type)

    url = reverse("expenses:name_update", kwargs={"pk": other_name.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert other_name.title not in actual
    assert other_type.title not in actual


def _name_options(response):
    content = response.content.decode()
    # the empty choice opens every rendered dropdown, so a blank page is not "no names"
    assert content.lstrip().startswith('<option value="">- Pasirinkti -</option>')
    return sorted(re.findall(r'<option value="\d+">([^<]*)</option>', content))


@pytest.mark.usefixtures("type_with_two_names")
@pytest.mark.parametrize(
    "expense_type",
    [
        pytest.param("", id="empty_parent"),
        pytest.param("abc", id="type_not_integer"),
    ],
)
def test_load_expense_name_without_a_type_is_missing(client_logged, expense_type):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": expense_type})

    assert _name_options(response) == []


@pytest.mark.parametrize(
    "names, type_field, params, expected",
    [
        pytest.param(
            [{"title": "N"}],
            "form-3-expense_type",
            {"prefix": "form-3"},
            ["N"],
            id="prefix",
        ),
        pytest.param(
            [{"title": "N"}],
            "expense_type",
            {"prefix": "form-3"},
            [],
            id="prefix_reads_only_prefixed_field",
        ),
        pytest.param(
            [
                {"title": "N-default"},
                {"title": "N-1999", "valid_for": 1999},
                {"title": "N-1998", "valid_for": 1998},
            ],
            "expense_type",
            {},
            ["N-1999", "N-default"],
            id="user_year",
        ),
        pytest.param(
            [{"title": "N-default"}, {"title": "N-2005", "valid_for": 2005}],
            "expense_type",
            {"year": 2005},
            ["N-2005", "N-default"],
            id="year",
        ),
        pytest.param(
            [{"title": "N-2005", "valid_for": 2005}],
            "expense_type",
            {"year": 2006},
            [],
            id="year_excludes_other_year",
        ),
        pytest.param(
            [{"title": "N", "valid_for": 2005}],
            "form-3-expense_type",
            {"prefix": "form-3", "year": 2005},
            ["N"],
            id="prefix_and_year",
        ),
        pytest.param(
            [{"title": "N"}],
            "expense_type",
            {"year": "abc"},
            ["N"],
            id="year_not_integer_falls_back_to_user_year",
        ),
    ],
)
def test_load_expense_name_reads_prefix_and_year(
    client_logged, names, type_field, params, expected
):
    expense_type = ExpenseTypeFactory()
    for name in names:
        ExpenseNameFactory(parent=expense_type, **name)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {type_field: expense_type.pk} | params)

    assert _name_options(response) == expected


def test_load_expense_name_other_journal_type_yields_no_names(
    client_logged, second_user
):
    other_type = ExpenseTypeFactory(journal=second_user.journal)
    ExpenseNameFactory(title="N", parent=other_type)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": other_type.pk})

    assert _name_options(response) == []


@pytest.mark.parametrize(
    "query",
    [
        pytest.param({"search": "xxx"}, id="no_match"),
        pytest.param({}, id="no_search_given"),
    ],
)
def test_search_not_found(client_logged, query):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, query)
    actual = response.content.decode("utf-8")

    assert '<div class="alert">Nieko nerasta</div>' in clean_content(actual)
    assert "alert-warning" not in actual


def test_search_found(client_logged):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, {"search": "type"})
    actual = response.content.decode("utf-8")

    assert '<td class="text-left expense-ordinary">1999-01-01</td>' in actual
    assert '<td class="text-left cell-padding remark">Remark</td>' in actual


@pytest.mark.parametrize(
    "query, expected",
    [
        pytest.param({"search": "type"}, 50, id="first_page"),
        pytest.param({"page": 2, "search": "type"}, 1, id="second_page"),
    ],
)
def test_search_pagination(client_logged, query, expected):
    account = AccountFactory()
    expense_type = ExpenseTypeFactory()
    expense_name = ExpenseNameFactory()
    expenses = ExpenseFactory.build_batch(
        51, account=account, expense_type=expense_type, expense_name=expense_name
    )
    models.Expense.objects.bulk_create(expenses)

    url = reverse("expenses:search")
    content = client_logged.get(url, query).content.decode()

    assert content.count("<tr hx-get=") == expected
    # a page of the search swaps into #data like the first one
    links = re.findall(
        r'<a role="button"[^>]*hx-get="/expenses/search/\?page=[^>]*>', content
    )
    assert links
    assert all('hx-target="#data"' in link for link in links)


def test_search_totals_row_sums_the_quantity_and_price_under_their_columns(
    client_logged,
):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2, remark="xxx")
    ExpenseFactory(price=300, quantity=3, remark="xxx")

    url = reverse("expenses:search")
    actual = client_logged.get(url, {"search": "xxx"}).content.decode("utf-8")

    assert re.search(
        r'<tfoot>\s*<tr class="main__total">\s*<td class="text-left">Viso</td>'
        r"\s*<td></td>\s*<td></td>\s*<td>5</td>\s*<td>5,00</td>\s*"
        r'<td colspan="5"></td>',
        actual,
    )
    assert "<caption>Vidutinė vieneto kaina: 1,00</caption>" in actual
    assert "alert-warning" not in actual


def test_search_statistic_not_found(client_logged):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2)
    ExpenseFactory(price=300, quantity=3)

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "xxx"})
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual
    assert "search-statistic" not in actual


def _get(view):
    return view.get(view.request)


def _import_save(rf, user):
    request = rf.post("/")
    request.user = user

    # the receipt form's account read raises first
    with patch.object(expenses_import, "ReviewReceiptForm"):
        return expenses_import.ImportSave().post(request)


class _Names(ExpenseNameChoicesMixin):
    def __init__(self, user):
        self.user = user


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, expense_views.TabIndex).get_context_data(),
            id="tab_index",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, TabTypes).get_context_data(), id="tab_types"
        ),
        pytest.param(lambda rf, u: view_for(rf, u, Lists).get_queryset(), id="list"),
        pytest.param(
            lambda rf, u: _get(view_for(rf, u, LoadExpenseName, "/?expense_type=1")),
            id="load_expense_name",
        ),
        pytest.param(lambda rf, u: _Names(u).names_year(), id="names_year"),
        pytest.param(lambda rf, u: _import_save(rf, u), id="import_save"),
        pytest.param(
            lambda rf, u: ReviewLineForm(user=u, year=1999), id="review_line_form"
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, call):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)
