import json
import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.tests.utils import (
    quick_add_pills,
    stat_card_tooltips,
    stat_cards,
    view_for,
)
from .. import models, views
from ..tabs import TABS
from .factories import Income, IncomeFactory, IncomeTypeFactory

pytestmark = pytest.mark.django_db


def _update_data(income, on="1999-12-31"):
    return {
        "price": "150",
        "date": on,
        "remark": "Pastaba",
        "account": income.account.pk,
        "income_type": income.income_type.pk,
    }


@time_machine.travel("2000-01-01")
@pytest.mark.parametrize(
    "url_of, trigger, expected_of",
    [
        (
            lambda i: reverse("incomes:new"),
            "reload",
            lambda i: ['<input type="text" name="date" value="1999-01-01"'],
        ),
        (
            lambda i: reverse("incomes:update", kwargs={"pk": i.pk}),
            "",
            lambda i: [
                '<input type="text" name="date" value="1999-01-01"',
                '<input type="text" name="price" value="77.77"',
                f'<option value="{i.account.pk}" selected>Account1</option>',
                f'<option value="{i.income_type.pk}" selected>Income Type</option>',
                "Pastaba</textarea>",
            ],
        ),
    ],
    ids=["new", "update"],
)
def test_income_load_form(client_logged, url_of, trigger, expected_of):
    income = IncomeFactory(price=7777, remark="Pastaba")
    url = url_of(income)

    actual = client_logged.get(url).content.decode("utf-8")

    assert re.search(
        rf'id="generic-form"[^>]*hx-post="{url}"[^>]*data-hx-trigger-form="{trigger}"',
        actual,
    )
    for text in expected_of(income):
        assert text in actual


@pytest.mark.parametrize(
    "name, data, row",
    [
        (
            "incomes:new",
            {"date": "1999-01-01", "price": "111"},
            r'<td class="text-left">1999-01-01</td>\s*'
            r'<td class="text-left">Income Type</td>\s*'
            r'<td class="text-left">Account1</td>\s*'
            r'<td class="text-left"></td>\s*<td class="main__figure">111,00</td>',
        ),
        (
            "incomes:type_new",
            {"title": "TTT", "type": "salary"},
            r'<td class="text-left">TTT</td>',
        ),
        (
            "incomes:type_update",
            {"title": "TTT", "type": "other"},
            r'<td class="text-left">TTT</td>',
        ),
    ],
    ids=["income", "type", "type_update"],
)
def test_save_follows_to_the_list_showing_the_row(client_logged, name, data, row):
    income_type = IncomeTypeFactory()
    # the type forms ignore the account and income type they do not ask for
    posted = data | {"account": AccountFactory().pk, "income_type": income_type.pk}
    kwargs = {"pk": income_type.pk} if name == "incomes:type_update" else {}

    response = client_logged.post(reverse(name, kwargs=kwargs), posted, follow=True)

    assert re.search(row, response.content.decode("utf-8"))


def test_income_save_htmx_answers_204_and_stores_the_row(client_logged):
    a = AccountFactory()
    i = IncomeTypeFactory()

    data = {"date": "1999-01-01", "price": "111", "account": a.pk, "income_type": i.pk}

    url = reverse("incomes:new")

    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    actual = models.Income.objects.get()
    assert response.status_code == 204
    assert "HX-Trigger" not in response.headers
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 111 * 100
    assert actual.account == a
    assert actual.income_type == i


@pytest.mark.parametrize(
    "name, data, model, error",
    [
        (
            "incomes:new",
            {"date": "x", "price": "x", "account": "x", "income_type": "x"},
            models.Income,
            "Įveskite skaičių.",
        ),
        (
            "incomes:type_new",
            {"title": ""},
            models.IncomeType,
            "Šis laukas yra privalomas.",
        ),
    ],
    ids=["income", "type"],
)
def test_invalid_data_shows_the_error_and_saves_nothing(
    client_logged, name, data, model, error
):
    response = client_logged.post(reverse(name), data)

    assert error in response.content.decode()
    assert model.objects.count() == 0


def test_income_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    a = AccountFactory(journal=j, title="a")
    it = IncomeTypeFactory(title="yyy", journal=j)
    obj = IncomeFactory(income_type=it, price=666, account=a)

    url = reverse("incomes:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_income_update_htmx_response(client_logged):
    income = IncomeFactory()

    url = reverse("incomes:update", kwargs={"pk": income.pk})
    response = client_logged.post(
        url, _update_data(income), **{"HTTP_HX-Request": "true"}
    )

    assert response.status_code == 204
    assert response.headers["HX-Trigger"] == '{"reload": {}}'


@pytest.mark.parametrize(
    "stored, posted, today",
    [
        (date(1999, 1, 1), "1999-12-31", "2000-03-03"),
        (date(1999, 1, 1), "2010-12-31", "2010-06-01"),
        (date(1974, 12, 12), "1997-12-12", "2000-03-03"),
    ],
    ids=["same_year", "another_year", "past_record"],
)
def test_income_update_stores_the_posted_row(client_logged, stored, posted, today):
    income = IncomeFactory(date=stored)
    url = reverse("incomes:update", kwargs={"pk": income.pk})

    with time_machine.travel(today):
        client_logged.post(url, _update_data(income, posted), follow=True)

    actual = models.Income.objects.get(pk=income.pk)
    assert actual.date == date.fromisoformat(posted)
    assert actual.price == 150 * 100
    assert actual.account.title == "Account1"
    assert actual.income_type.title == "Income Type"
    assert actual.remark == "Pastaba"


def test_incomes_data_search_form(client_logged):
    url = reverse("incomes:tab_data")
    response = client_logged.get(url).content.decode("utf-8")

    search = reverse("incomes:search")
    assert '<input type="search" name="search"' in response
    assert re.search(rf'id="search-form"\s+hx-get="{search}"', response)


@pytest.mark.parametrize(
    "url, has_subnav",
    [("incomes:list", False), ("incomes:tab_data", True)],
    ids=["list", "tab_data"],
)
def test_incomes_list_shows_the_price_with_the_subnav_only_on_the_tab(
    client_logged, url, has_subnav
):
    IncomeFactory()

    content = client_logged.get(reverse(url)).content.decode()

    assert '<td class="main__figure">10,00</td>' in content
    assert ('<nav class="subnav">' in content) is has_subnav


def test_list_empty_state_names_the_selected_year(client_logged):
    actual = client_logged.get(reverse("incomes:list")).content.decode("utf-8")

    assert re.search(
        r'<div class="alert[^"]*">\s*<b>1999</b> metais įrašų nėra\.', actual
    )


@pytest.mark.parametrize(
    "url, query",
    [("incomes:list", {}), ("incomes:search", {"search": "Alga"})],
    ids=["list", "search"],
)
def test_list_and_search_render_the_same_type_and_account_cells(
    client_logged, url, query
):
    IncomeFactory(
        income_type=IncomeTypeFactory(title="Alga"),
        account=AccountFactory(title="Kasa"),
    )

    content = client_logged.get(reverse(url), query).content.decode()

    assert '<td class="text-left">Alga</td>' in content
    assert '<td class="text-left">Kasa</td>' in content


def test_view_incomes_delete_load_form(client_logged):
    p = IncomeFactory()

    url = reverse("incomes:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert re.search(
        rf'<form method="POST" id="delete-form"[^>]*hx-post="{url}"', actual
    )
    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_view_incomes_delete(client_logged):
    p = IncomeFactory()

    assert models.Income.objects.all().count() == 1
    url = reverse("incomes:delete", kwargs={"pk": p.pk})

    response = client_logged.post(url, {}, follow=True)

    assert response.status_code == 204

    assert models.Income.objects.all().count() == 0


def test_incomes_delete_other_journal_get_form(client_logged, second_user):
    it2 = IncomeTypeFactory(title="yyy", journal=second_user.journal)
    i2 = IncomeFactory(income_type=it2, price=666)

    url = reverse("incomes:delete", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_incomes_delete_other_journal_post_form(client_logged, second_user):
    it2 = IncomeTypeFactory(title="yyy", journal=second_user.journal)
    i2 = IncomeFactory(income_type=it2, price=666)

    url = reverse("incomes:delete", kwargs={"pk": i2.pk})
    client_logged.post(url)

    assert Income.objects.all().count() == 1


@pytest.mark.parametrize(
    "name, with_pk",
    [("incomes:type_new", False), ("incomes:type_update", True)],
    ids=["new", "update"],
)
def test_type_load_form(client_logged, name, with_pk):
    kwargs = {"pk": IncomeTypeFactory().pk} if with_pk else {}
    url = reverse(name, kwargs=kwargs)

    response = client_logged.get(url)
    actual = response.content.decode()

    assert re.search(
        rf'id="generic-form"[^>]*hx-post="{url}"[^>]*data-hx-trigger-form=""', actual
    )


def test_type_save_htmx_trigger_value(client_logged):
    url = reverse("incomes:type_new")
    data = {"title": "TTT", "type": "salary"}

    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


def test_income_type_not_load_other_journal(client_logged, second_user):
    IncomeTypeFactory(title="xxx")
    obj = IncomeTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("incomes:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "search, shown",
    [
        ("xxx", r'<div class="alert">\s*Nieko nerasta\s*</div>'),
        (
            "1999 type",
            r'<td class="text-left">1999-01-01</td>\s*'
            r'<td class="text-left">Income Type</td>\s*'
            r'<td class="text-left">Account1</td>\s*'
            r'<td class="text-left">remark</td>',
        ),
    ],
    ids=["not_found", "found"],
)
def test_search_answers_the_matches_or_nothing_found(client_logged, search, shown):
    IncomeFactory()

    response = client_logged.get(reverse("incomes:search"), {"search": search})

    assert re.search(shown, response.content.decode("utf-8"))


@pytest.mark.parametrize(
    "query, expected",
    [({"search": "1999 type"}, 50), ({"page": 2, "search": "type"}, 1)],
    ids=["first_page", "second_page"],
)
def test_search_pagination(client_logged, query, expected):
    a = AccountFactory()
    t = IncomeTypeFactory()
    i = IncomeFactory.build_batch(51, account=a, income_type=t)
    Income.objects.bulk_create(i)

    url = reverse("incomes:search")
    response = client_logged.get(url, query)
    actual = response.content.decode("utf-8")

    assert actual.count('<td class="text-left">Income Type</td>') == expected


def test_search_page_links_keep_the_search(client_logged):
    a = AccountFactory()
    t = IncomeTypeFactory()
    Income.objects.bulk_create(IncomeFactory.build_batch(51, account=a, income_type=t))

    url = reverse("incomes:search")
    content = client_logged.get(url, {"search": "type"}).content.decode("utf-8")

    # the other page's number and the next arrow
    page_link = (
        r'<a role="button"[^>]*hx-get="/incomes/search/\?page=2&search=type"'
        r'[^>]* hx-target="#data"'
    )
    assert len(re.findall(page_link, content)) == 2


def test_an_income_row_opens_its_own_forms(client_logged):
    income = IncomeFactory()

    actual = client_logged.get(reverse("incomes:list")).content.decode("utf-8")

    rows = re.findall(
        r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"'
        r'.*?<td class="edit-col">\s*<a role="button" hx-get="([^"]*)"'
        r'.*?<td class="delete-col">\s*<a role="button" hx-get="([^"]*)"',
        actual,
        re.DOTALL,
    )
    update = f"/incomes/update/{income.pk}/"
    assert rows == [(update, update, f"/incomes/delete/{income.pk}/")]


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

    title = {"index": "Apžvalga", "data": "Duomenys", "types": "Rūšys"}[tab.name]
    assert '<nav class="subnav">' not in content
    assert f"<title>Pajamos | {title}</title>" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_history_restore_rebuilds_the_whole_page(client_logged, tab):
    headers = {"HX-Request": "true", "HX-History-Restore-Request": "true"}

    content = client_logged.get(tab.url, headers=headers).content.decode()

    assert '<nav class="subnav">' in content


@pytest.mark.parametrize(
    "headers", [{"HX-Request": "true"}, {}], ids=["fragment", "page"]
)
@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_only_the_open_tab_reloads_on_a_saved_income(client_logged, tab, headers):
    # Types reloads the sort it shows
    query = {"types": "?order=title"}.get(tab.name, "")

    content = client_logged.get(tab.url, headers=headers).content.decode()

    listener = (
        f'hx-get="{tab.url}{query}" hx-target="#tab_content"'
        ' hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("incomes:index")).content.decode()

    for tab in TABS:
        assert re.search(
            rf'<button\s+id="tab-{tab.name}"[^>]*hx-get="{re.escape(tab.url)}"',
            content,
        )


@pytest.mark.parametrize(
    "url_name, heading",
    [
        pytest.param(
            "incomes:tab_types", "<title>Pajamos | Rūšys</title>", id="browser_title"
        ),
        pytest.param(
            "incomes:tab_index",
            '<h2 class="panel__title">Pajamos per mėnesį</h2>',
            id="months_panel_title",
        ),
    ],
)
def test_tab_states_its_title(client_logged, url_name, heading):
    content = client_logged.get(reverse(url_name)).content.decode()

    assert heading in content


@time_machine.travel("1999-09-15")
def test_types_tab_states_each_type_in_a_table(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    IncomeTypeFactory(title="Kita")
    IncomeFactory(date=date(1999, 2, 5), price=90_000, income_type=alga)
    IncomeFactory(date=date(1998, 2, 5), price=70_000, income_type=alga)

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert '<td class="text-left">Kita</td>' in content
    assert re.search(
        r'>Alga</td>\s*<td class="main__figure">900</td>\s*'
        r'<td class="main__figure">700</td>\s*<td class="main__figure">100%</td>\s*'
        r"<td>1999-02-05</td>",
        content,
    )
    assert re.search(
        r'<tr class="main__total">\s*<td class="text-left">Viso</td>\s*'
        r'<td class="main__figure">900</td>\s*<td class="main__figure">700</td>\s*'
        r'<td class="main__figure">100%</td>',
        content,
    )
    assert "c-accordion" not in content and 'class="accordion"' not in content


@time_machine.travel("2000-09-15")
def test_types_tab_of_a_past_year_shows_its_own_last_income(main_user, client_logged):
    main_user.year = 1999
    main_user.save()
    alga = IncomeTypeFactory(title="Alga")
    IncomeFactory(date=date(1999, 5, 5), income_type=alga)
    IncomeFactory(date=date(2000, 2, 2), income_type=alga)

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert "<td>1999-05-05</td>" in content
    assert "<td>2000-02-02</td>" not in content


def test_types_tab_edits_each_type_from_its_row(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    link = reverse("incomes:type_update", kwargs={"pk": alga.pk})

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert f'<tr hx-get="{link}" hx-trigger="dblclick"' in content
    assert f'hx-get="{link}" hx-target="#mainModal" class="edit"' in content


@time_machine.travel("1999-09-15")
def test_types_tab_sorts_by_the_asked_column(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    zeta = IncomeTypeFactory(title="Zeta")
    IncomeFactory(date=date(1999, 2, 5), price=10_000, income_type=alga)
    IncomeFactory(date=date(1999, 2, 5), price=90_000, income_type=zeta)
    url = reverse("incomes:tab_types")

    by_title = client_logged.get(url).content.decode()
    by_share = client_logged.get(url, {"order": "share"}).content.decode()

    title_cells = r'<td class="text-left">([^<]*)</td>'
    assert re.findall(title_cells, by_title) == ["Alga", "Zeta", "Viso"]
    assert re.findall(title_cells, by_share) == ["Zeta", "Alga", "Viso"]


@pytest.mark.parametrize("order", ["share", "title"])
def test_types_tab_sort_links_and_reload_carry_only_the_order(client_logged, order):
    url = reverse("incomes:tab_types")

    content = client_logged.get(url, {"order": order}).content.decode()

    # pushed, so a reload keeps the sort
    assert '<thead class="sortable-header-row" hx-push-url:inherited="true">' in content
    for key, label in (
        ("title", "Pajamų rūšis"),
        ("this_year", "Šiemet"),
        ("last_year", "Pernai"),
        ("share", "Dalis"),
        ("last_income", "Paskutinį kartą"),
    ):
        drawn = (
            f'<a role="button" hx-get="{url}?order={key}"'
            f' hx-target="#tab_content">{label}</a>'
        )
        if key == order:
            drawn = f"<span>{label}</span>"
        assert drawn in content
    assert re.search(r'<th class="text-left">\s*<(span|a [^>]*)>Pajamų', content)
    # a save reloads the sort shown
    assert f'<div hx-get="{url}?order={order}" hx-target="#tab_content"' in content


def test_types_tab_draws_no_groups(client_logged):
    IncomeTypeFactory(title="Alga", type="salary")
    IncomeTypeFactory(title="Kita", type="other")

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert "table-group-divider" not in content


@time_machine.travel("1999-09-15")
def test_overview_states_the_year_in_three_cards(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    IncomeFactory(date=date(1999, 1, 5), price=90_000, income_type=alga)
    IncomeFactory(date=date(1998, 1, 5), price=80_000, income_type=alga)
    IncomeFactory(date=date(1998, 12, 5), price=5_000, income_type=alga)

    content = client_logged.get(reverse("incomes:tab_index")).content.decode()

    assert stat_cards(content) == [
        ("Šiais metais", "900", "Pernai 800"),
        ("Per mėnesį", "100", "9 mėnesiai"),
        ("Didžiausia rūšis", "Alga", "100% metų sumos"),
    ]
    assert stat_card_tooltips(content) == [
        "Metų suma, padalinta iš prabėgusių mėnesių",
        "Didžiausią šių metų dalį sudaranti pajamų rūšis",
    ]


@time_machine.travel("1999-09-15")
def test_overview_charts_the_year_against_last_year_to_the_same_day(client_logged):
    IncomeFactory(date=date(1999, 2, 5), price=90_000)
    IncomeFactory(date=date(1998, 9, 10), price=80_000)
    IncomeFactory(date=date(1998, 9, 20), price=5_000)

    content = client_logged.get(reverse("incomes:tab_index")).content.decode()
    chart = json.loads(
        re.search(r'id="chart-months-data"[^>]*>(.*?)</script>', content)[1]
    )
    data = {series["name"]: series["data"] for series in chart["series"]}

    assert data["1999"] == [0.0, 900.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert data["1998"][8] == 800.0


def test_quick_add_offers_its_pills(client_logged):
    content = client_logged.get(reverse("incomes:index")).content.decode()

    assert quick_add_pills(content) == [
        ("button", "types", 'hx-get="/incomes/type/new/"', "Pridėti pajamų rūšį"),
        ("button", "", 'hx-get="/incomes/new/"', "Pridėti pajamas"),
    ]


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_the_pill_stays_outside_the_swapped_tab(client_logged, tab):
    content = client_logged.get(tab.url, headers={"HX-Request": "true"}).content

    assert b'class="quick-add' not in content


def _tab_queries(client, tab):
    with CaptureQueriesContext(connection) as queries:
        client.get(tab.url, headers={"HX-Request": "true"})
    return len(queries)


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_query_count_does_not_grow_with_the_incomes(client_logged, tab):
    for i in range(2):
        IncomeFactory(income_type=IncomeTypeFactory(title=f"T{i}"))
    two = _tab_queries(client_logged, tab)

    for i in range(2, 6):
        IncomeFactory(income_type=IncomeTypeFactory(title=f"T{i}"))
    six = _tab_queries(client_logged, tab)

    assert six == two


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabIndex).get_context_data(),
            id="tab_index",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.Lists).get_queryset(), id="list"
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabTypes).get_context_data(),
            id="tab_types",
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, call):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)
