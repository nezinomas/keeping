import json
import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse

from ...accounts.tests.factories import AccountFactory
from .. import models, views
from ..tabs import TABS
from .factories import Income, IncomeFactory, IncomeTypeFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                      Incomes
# ----------------------------------------------------------------------------
def test_incomes_index_func():
    view = resolve("/incomes/")

    assert views.TabIndex == view.func.view_class


def test_incomes_lists_func():
    view = resolve("/incomes/lists/")

    assert views.Lists == view.func.view_class


def test_incomes_data_func():
    view = resolve("/incomes/data/")

    assert views.TabData == view.func.view_class


def test_incomes_new_func():
    view = resolve("/incomes/new/")

    assert views.New == view.func.view_class


def test_incomes_update_func():
    view = resolve("/incomes/update/1/")

    assert views.Update == view.func.view_class


def test_types_tab_func():
    view = resolve("/incomes/types/")

    assert views.TabTypes == view.func.view_class


def test_types_new_func():
    view = resolve("/incomes/type/new/")

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve("/incomes/type/update/1/")

    assert views.TypeUpdate == view.func.view_class


@time_machine.travel("2000-01-01")
def test_income_load_form(client_logged):
    url = reverse("incomes:new")

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert "1999-01-01" in actual


def test_income_save(client_logged):
    a = AccountFactory()
    i = IncomeTypeFactory()

    data = {"date": "1999-01-01", "price": "111", "account": a.pk, "income_type": i.pk}

    url = reverse("incomes:new")

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "111" in actual
    assert "Account1" in actual
    assert "Income Type" in actual


def test_income_save_status_code(client_logged):
    a = AccountFactory()
    i = IncomeTypeFactory()

    data = {"date": "1999-01-01", "price": "111", "account": a.pk, "income_type": i.pk}

    url = reverse("incomes:new")

    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.status_code == 204


def test_income_save_invalid_data(client_logged):
    data = {"date": "x", "price": "x", "account": "x", "income_type": "x"}

    url = reverse("incomes:new")

    response = client_logged.post(url, data)

    actual = response.context["form"]

    assert not actual.is_valid()


def test_income_load_update_form(client_logged):
    i = IncomeFactory(price=7777)
    url = reverse("incomes:update", kwargs={"pk": i.pk})

    response = client_logged.get(url)

    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert '<input type="text" name="price" value="77.77"' in actual
    assert '<option value="1" selected>Account1</option>' in actual
    assert '<option value="1" selected>Income Type</option>' in actual
    assert "remark" in actual


def test_income_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    a = AccountFactory(journal=j, title="a")
    it = IncomeTypeFactory(title="yyy", journal=j)
    obj = IncomeFactory(income_type=it, price=666, account=a)

    url = reverse("incomes:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_income_update_to_another_year(client_logged):
    income = IncomeFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "remark": "Pastaba",
        "account": 1,
        "income_type": 1,
    }
    url = reverse("incomes:update", kwargs={"pk": income.pk})
    client_logged.post(url, data, follow=True)

    actual = models.Income.objects.get(pk=income.pk)
    assert actual.date == date(2010, 12, 31)


def test_income_update(client_logged):
    income = IncomeFactory()

    data = {
        "price": "150",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "income_type": 1,
    }
    url = reverse("incomes:update", kwargs={"pk": income.pk})
    client_logged.post(url, data, follow=True)

    actual = models.Income.objects.get(pk=income.pk)
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 150 * 100
    assert actual.remark == "Pastaba"


def test_income_update_status_code(client_logged):
    income = IncomeFactory()

    data = {
        "price": "150",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "income_type": 1,
    }
    url = reverse("incomes:update", kwargs={"pk": income.pk})
    request = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert request.status_code == 204


def test_income_update_htmx_trigger_value(client_logged):
    income = IncomeFactory()

    data = {
        "price": "150",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "income_type": 1,
    }
    url = reverse("incomes:update", kwargs={"pk": income.pk})
    request = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert request.headers["HX-Trigger"] == '{"reload": {}}'


@time_machine.travel("2000-03-03")
def test_income_update_past_record(main_user, client_logged):
    main_user.year = 2000
    i = IncomeFactory(date=date(1974, 12, 12))

    data = {
        "price": "150",
        "date": "1997-12-12",
        "remark": "Pastaba",
        "account": 1,
        "income_type": 1,
    }
    url = reverse("incomes:update", kwargs={"pk": i.pk})
    client_logged.post(url, data, follow=True)

    actual = models.Income.objects.get(pk=i.pk)
    assert actual.date == date(1997, 12, 12)
    assert actual.price == 150 * 100
    assert actual.account.title == "Account1"
    assert actual.income_type.title == "Income Type"
    assert actual.remark == "Pastaba"


def test_incomes_data_search_form(client_logged):
    url = reverse("incomes:tab_data")
    response = client_logged.get(url).content.decode("utf-8")

    assert '<input type="search" name="search"' in response
    assert reverse("incomes:search") in response


def test_incomes_list_renders_the_rows_alone(client_logged):
    IncomeFactory()

    content = client_logged.get(reverse("incomes:list")).content.decode()

    assert "10,00</td>" in content
    assert '<nav class="subnav">' not in content


def test_incomes_list_price_value(client_logged):
    IncomeFactory()

    url = reverse("incomes:tab_data")
    response = client_logged.get(url).content.decode("utf-8")

    assert "10,00</td>" in response


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


# -------------------------------------------------------------------------------------
#                                                                         Income Delete
# -------------------------------------------------------------------------------------
def test_view_incomes_delete_func():
    view = resolve("/incomes/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_incomes_delete_200(client_logged):
    p = IncomeFactory()

    url = reverse("incomes:delete", kwargs={"pk": p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


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


# ----------------------------------------------------------------------------
#                                                                 Income Type
# ----------------------------------------------------------------------------
def test_type_load_form_200(client_logged):
    url = reverse("incomes:type_new")

    response = client_logged.get(url)

    assert response.status_code == 200


def test_type_load_form(client_logged):
    url = reverse("incomes:type_new")

    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_type_save(client_logged):
    data = {
        "title": "TTT",
        "type": "salary",
    }

    url = reverse("incomes:type_new")

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_type_save_htmx_trigger_value(client_logged):
    url = reverse("incomes:type_new")
    data = {"title": "TTT", "type": "salary"}

    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Trigger"] == '{"reload": {}}'


def test_type_save_invalid_data(client_logged):
    data = {"title": ""}

    url = reverse("incomes:type_new")

    response = client_logged.post(url, data)

    form = response.context.get("form")

    assert not form.is_valid()


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


def test_view_index_200(client_logged):
    response = client_logged.get("/incomes/")

    assert response.status_code == 200


# -------------------------------------------------------------------------------------
#                                                                        Incomes Search
# -------------------------------------------------------------------------------------
def test_search_func():
    view = resolve("/incomes/search/")

    assert views.Search == view.func.view_class


def test_search_get_200(client_logged):
    url = reverse("incomes:search")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_not_found(client_logged):
    IncomeFactory()

    url = reverse("incomes:search")
    response = client_logged.get(url, {"search": "xxx"})
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual


def test_search_found(client_logged):
    IncomeFactory()

    url = reverse("incomes:search")
    response = client_logged.get(url, {"search": "1999 type"})
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "remark" in actual


def test_search_pagination_first_page(client_logged):
    a = AccountFactory()
    t = IncomeTypeFactory()
    i = IncomeFactory.build_batch(51, account=a, income_type=t)
    Income.objects.bulk_create(i)

    url = reverse("incomes:search")
    response = client_logged.get(url, {"search": "1999 type"})
    actual = response.content.decode("utf-8")

    assert actual.count("Income Type") == 50


def test_search_pagination_second_page(client_logged):
    a = AccountFactory()
    t = IncomeTypeFactory()
    i = IncomeFactory.build_batch(51, account=a, income_type=t)
    Income.objects.bulk_create(i)

    url = reverse("incomes:search")

    response = client_logged.get(url, {"page": 2, "search": "type"})
    actual = response.content.decode("utf-8")

    assert actual.count("Income Type") == 1


# -------------------------------------------------------------------------------------
#                                                                                 Tabs
# -------------------------------------------------------------------------------------
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


def test_types_tab_lists_the_income_types(client_logged):
    IncomeTypeFactory(title="Alga")

    content = client_logged.get(reverse("incomes:tab_types")).content.decode()

    assert "Alga" in content


@time_machine.travel("1999-09-15")
def test_overview_states_the_year_in_three_cards(client_logged):
    alga = IncomeTypeFactory(title="Alga")
    IncomeFactory(date=date(1999, 1, 5), price=90_000, income_type=alga)
    IncomeFactory(date=date(1998, 1, 5), price=80_000, income_type=alga)
    IncomeFactory(date=date(1998, 12, 5), price=5_000, income_type=alga)

    content = client_logged.get(reverse("incomes:tab_index")).content.decode()

    assert "Didžiausia rūšis" in content
    assert "Alga" in content
    assert "Pernai 800,00" in content
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
