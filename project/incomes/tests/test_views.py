import json
import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from .. import models
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
def test_income_load_form(client_logged):
    url = reverse("incomes:new")

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert 'data-hx-trigger-form="reload"' in actual
    assert "1999-01-01" in actual


@pytest.mark.parametrize(
    "name, data, shown",
    [
        (
            "incomes:new",
            {"date": "1999-01-01", "price": "111"},
            ["1999-01-01", "111", "Account1", "Income Type"],
        ),
        ("incomes:type_new", {"title": "TTT", "type": "salary"}, ["TTT"]),
    ],
    ids=["income", "type"],
)
def test_save_follows_to_the_list_showing_the_row(client_logged, name, data, shown):
    # the type form ignores the account and income type it does not ask for
    posted = data | {
        "account": AccountFactory().pk,
        "income_type": IncomeTypeFactory().pk,
    }

    response = client_logged.post(reverse(name), posted, follow=True)

    actual = response.content.decode("utf-8")
    for text in shown:
        assert text in actual


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


def test_income_load_update_form(client_logged):
    i = IncomeFactory(price=7777, remark="Pastaba")
    url = reverse("incomes:update", kwargs={"pk": i.pk})

    response = client_logged.get(url)

    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert '<input type="text" name="price" value="77.77"' in actual
    assert f'<option value="{i.account.pk}" selected>Account1</option>' in actual
    assert f'<option value="{i.income_type.pk}" selected>Income Type</option>' in actual
    assert "Pastaba</textarea>" in actual


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

    assert '<input type="search" name="search"' in response
    assert reverse("incomes:search") in response


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

    assert "10,00</td>" in content
    assert ('<nav class="subnav">' in content) is has_subnav


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

    assert f'hx-post="{url}"' in actual
    assert '<form method="POST"' in actual
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


def test_type_load_form(client_logged):
    url = reverse("incomes:type_new")

    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual
    assert 'data-hx-trigger-form=""' in actual


def test_type_save_htmx_trigger_value(client_logged):
    url = reverse("incomes:type_new")
    data = {"title": "TTT", "type": "salary"}

    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


def test_type_update_load_form(client_logged):
    income = IncomeTypeFactory()

    url = reverse("incomes:type_update", kwargs={"pk": income.pk})

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_type_update(client_logged):
    income = IncomeTypeFactory()

    data = {"title": "TTT", "type": "other"}
    url = reverse("incomes:type_update", kwargs={"pk": income.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_income_type_not_load_other_journal(client_logged, second_user):
    IncomeTypeFactory(title="xxx")
    obj = IncomeTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("incomes:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "search, shown",
    [("xxx", ["Nieko nerasta"]), ("1999 type", ["1999-01-01", "remark"])],
    ids=["not_found", "found"],
)
def test_search_answers_the_matches_or_nothing_found(client_logged, search, shown):
    IncomeFactory()

    response = client_logged.get(reverse("incomes:search"), {"search": search})

    actual = response.content.decode("utf-8")
    for text in shown:
        assert text in actual


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

    assert actual.count("Income Type") == expected


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged, tab):
    content = client_logged.get(tab.url).content.decode()

    assert '<nav class="subnav">' in content
    assert "paper.min.css" in content
    assert 'class="paper-skin"' in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_url_requested_by_htmx_returns_the_fragment_alone(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    assert '<nav class="subnav">' not in content
    assert "<title>" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_history_restore_rebuilds_the_whole_page(client_logged, tab):
    headers = {"HX-Request": "true", "HX-History-Restore-Request": "true"}

    content = client_logged.get(tab.url, headers=headers).content.decode()

    assert '<nav class="subnav">' in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_only_the_open_tab_reloads_on_a_saved_income(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    listener = (
        f'hx-get="{tab.url}" hx-target="#tab_content" hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("incomes:index")).content.decode()

    for tab in TABS:
        assert f'hx-get="{tab.url}"' in content


def test_browser_title_names_the_open_tab(client_logged):
    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert "<title>Pajamos | Rūšys</title>" in content


@time_machine.travel("1999-09-15")
def test_types_tab_states_each_type_in_a_table(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    IncomeTypeFactory(title="Kita")
    IncomeFactory(date=date(1999, 2, 5), price=90_000, income_type=alga)

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert '<td class="text-left">Kita</td>' in content
    assert "<td>900</td>" in content
    assert "Paskutinį kartą" in content
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
    assert "2000-02-02" not in content


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

    assert by_title.index(">Alga<") < by_title.index(">Zeta<")
    assert by_share.index(">Zeta<") < by_share.index(">Alga<")


def test_types_tab_links_every_header_but_the_active_one(client_logged):
    url = reverse("incomes:tab_types")

    content = client_logged.get(url, {"order": "share"}).content.decode()

    assert '<thead class="sortable-header-row">' in content
    assert "<span>Dalis</span>" in content
    for key in ("title", "this_year", "last_year", "last_income"):
        assert f'hx-get="{url}?order={key}" hx-target="#tab_content"' in content
    assert f"{url}?order=share" not in content


def test_types_tab_draws_no_groups(client_logged):
    IncomeTypeFactory(title="Alga", type="salary")
    IncomeTypeFactory(title="Kita", type="other")

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert "table-group-divider" not in content


def test_the_add_type_pill_waits_for_the_types_tab(client_logged):
    link = reverse("incomes:type_new")

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    pill = f'class="quick-add__pill" hx-get="{link}"'

    assert f"x-show=\"tab === 'types'\" x-cloak {pill}" in content
    assert "Pridėti pajamų rūšį" in content


def test_overview_titles_the_months_panel(client_logged):
    content = client_logged.get(reverse("incomes:tab_index")).content.decode()

    assert '<h2 class="panel__title">Pajamos per mėnesį</h2>' in content


@time_machine.travel("1999-09-15")
def test_overview_states_the_year_in_three_cards(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    IncomeFactory(date=date(1999, 1, 5), price=90_000, income_type=alga)
    IncomeFactory(date=date(1998, 1, 5), price=80_000, income_type=alga)
    IncomeFactory(date=date(1998, 12, 5), price=5_000, income_type=alga)

    content = client_logged.get(reverse("incomes:tab_index")).content.decode()

    assert "Didžiausia rūšis" in content
    assert "Alga" in content
    assert "Pernai 800<" in content
    assert "9 mėnesiai" in content


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


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_every_tab_offers_one_add_income_pill(client_logged, tab):
    content = client_logged.get(tab.url).content.decode()
    link = reverse("incomes:new")

    assert content.count('class="quick-add__pill"') == 2
    assert content.count(f'class="quick-add__pill" hx-get="{link}"') == 1
    assert "Pridėti pajamas" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_the_pill_stays_outside_the_swapped_tab(client_logged, tab):
    content = client_logged.get(tab.url, headers={"HX-Request": "true"}).content

    assert b"quick-add" not in content


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
