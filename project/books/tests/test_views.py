import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from django.utils.translation import gettext as _

from ...users.tests.factories import UserFactory
from .. import models, views
from ..tabs import TABS
from .factories import Book, BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                         Tabs
# ----------------------------------------------------------------------------
def test_index_func():
    view = resolve("/books/")

    assert views.TabIndex == view.func.view_class


def test_data_func():
    view = resolve("/books/data/")

    assert views.TabData == view.func.view_class


def test_index_200(client_logged):
    url = reverse("books:index")
    response = client_logged.get(url)

    assert response.status_code == 200


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged, tab):
    content = client_logged.get(tab.url).content.decode()

    assert '<nav class="subnav">' in content
    assert "css/paper.min.css" in content
    assert "css/main.min.css" not in content
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
def test_only_the_open_tab_reloads_on_a_saved_book_or_goal(client_logged, tab):
    content = client_logged.get(
        tab.url, headers={"HX-Request": "true"}
    ).content.decode()

    listener = (
        f'hx-get="{tab.url}" hx-target="#tab_content"'
        ' hx-trigger="reload from:body, afterTarget from:body"'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode()

    for tab in TABS:
        assert f'hx-get="{tab.url}"' in content


@pytest.mark.parametrize(
    ("name", "title"), [("index", "Knygos | Apžvalga"), ("data", "Knygos | Duomenys")]
)
def test_browser_title_names_the_open_tab(client_logged, name, title):
    content = client_logged.get(reverse(f"books:tab_{name}")).content.decode()

    assert f"<title>{title}</title>" in content


def test_books_heads_the_page_where_only_a_reader_hears_it(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert f'<h1 class="visually-hidden">{_("Books")}</h1>' in content


def test_books_loads_the_paper_chart_theme(client_logged):
    """The chart wears the skin because this page pulls the theme in."""
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert "js/chart_paper.js" in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_books_adds_a_book_from_the_foot_of_every_tab(client_logged, tab):
    content = client_logged.get(tab.url).content.decode("utf-8")

    link = reverse("books:new")

    assert 'class="quick-add"' in content
    assert f'class="quick-add__pill" hx-get="{link}"' in content
    assert 'hx-target="#mainModal"' in content
    assert "Pridėti knygą" in content


def _tab_queries(client, tab):
    with CaptureQueriesContext(connection) as queries:
        client.get(tab.url)
    return len(queries)


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_query_count_does_not_grow_with_the_books(client_logged, tab):
    for _i in range(2):
        BookFactory()
    two = _tab_queries(client_logged, tab)

    for _i in range(2, 6):
        BookFactory()
    six = _tab_queries(client_logged, tab)

    assert six == two


# ----------------------------------------------------------------------------
#                                                                 Overview Tab
# ----------------------------------------------------------------------------
CARD = re.compile(
    r'trend-card__label">(.*?)</div>\s*<div class="trend-card__value[^"]*">'
    r'<span class="trend-card__figure"[^>]*>(.*?)</span>',
    re.S,
)


def test_overview_holds_cards_and_chart_and_no_table(client_logged):
    BookFactory()

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert content.index('class="stat-cards"') < content.index(
        'id="chart-finished-container"'
    )
    assert 'id="search-form"' not in content
    assert 'id="data"' not in content


def test_overview_titles_the_finished_books_panel(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert '<h2 class="panel__title">Perskaitytos knygos</h2>' in content


def test_overview_carries_the_chart_data(client_logged):
    BookFactory(ended=date(1999, 1, 1))

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert '<script id="chart-finished-data" type="application/json">' in content


@time_machine.travel("1999-07-18")
def test_overview_cards(client_logged):
    BookFactory()
    BookFactory()
    BookFactory(ended=date(1999, 2, 1))

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert content.count('class="trend-card"') == 3
    assert re.findall(CARD, content)[:2] == [("Perskaitytos", "1"), ("Skaitomos", "2")]


@time_machine.travel("1999-07-18")
def test_overview_cards_no_data(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert re.findall(CARD, content)[:2] == [("Perskaitytos", "0"), ("Skaitomos", "0")]


def test_overview_goal_pencil_opens_target_new(client_logged):
    """The pencil in the Goal card is the page's only way into the goal form."""
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    link = reverse("books:target_new")

    assert content.count(f'hx-get="{link}"') == 1
    assert f'<button type="button" class="trend-card__edit" hx-get="{link}"' in content
    assert re.search(
        rf'trend-card__edit" hx-get="{link}"[^>]*hx-target="#mainModal"', content
    )
    assert 'class="bi bi-pencil"' in content
    assert "Neįvestas tikslas" in content


def test_overview_goal_pencil_opens_target_update(client_logged):
    t = BookTargetFactory()

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    link = reverse("books:target_update", kwargs={"pk": t.pk})

    assert f'<button type="button" class="trend-card__edit" hx-get="{link}"' in content
    assert "Neįvestas tikslas" not in content


# ----------------------------------------------------------------------------
#                                                                     Data Tab
# ----------------------------------------------------------------------------
def test_data_tab_reads_search_then_table(client_logged):
    """The table is the variable-height thing, so nothing goes under it."""
    content = client_logged.get(reverse("books:tab_data")).content.decode("utf-8")

    assert '<input type="search" name="search"' in content
    assert 'id="id_search"' in content
    assert content.index('id="search-form"') < content.index('id="data"')
    assert 'id="chart-finished-container"' not in content


def test_data_tab_lists_this_year(client_logged):
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    content = client_logged.get(reverse("books:tab_data")).content.decode("utf-8")

    assert "This Year" in content
    assert "Old Book" not in content


def test_data_tab_all_records_lists_every_year(client_logged):
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse("books:tab_data")
    content = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert "Old Book" in content


def test_data_tab_all_records_reloads_all_records(client_logged):
    url = reverse("books:tab_data")
    content = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert f'hx-get="{url}?scope=all" hx-target="#tab_content"' in content


def test_navbar_all_records_opens_the_data_tab_on_every_year(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert f'href="{reverse("books:tab_data")}?scope=all"' in content


def test_all_records_pages_keep_their_scope(client_logged):
    Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    url = reverse("books:list")
    content = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert f'hx-get="{url}?page=2&scope=all"' in content


# ----------------------------------------------------------------------------
#                                                             Books Lists View
# ----------------------------------------------------------------------------
def test_lists_func():
    view = resolve("/books/lists/")

    assert views.Lists == view.func.view_class


def test_list_200(client_logged):
    url = reverse("books:list")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_list_with_data(client_logged):
    BookFactory()

    url = reverse("books:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Author" in actual
    assert "Book Title" in actual
    assert "Remark" in actual


def test_list_only_current_year(client_logged):
    BookFactory()
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31))

    url = reverse("books:list")
    response = client_logged.get(url)
    actual = response.context["object_list"]

    assert len(actual) == 1


def test_list_all_books(client_logged):
    BookFactory()
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31))

    url = reverse("books:list")
    response = client_logged.get(url, {"scope": "all"})
    actual = response.context["object_list"]
    assert len(actual) == 2


def test_list_all_books_lists_another_year(client_logged):
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse("books:list")
    actual = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert "Old Book" in actual
    assert "1974-01-01" in actual


def test_list_empty_state_names_the_year(client_logged):
    url = reverse("books:list")
    actual = client_logged.get(url).content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra" in actual


def test_list_all_books_empty_state_does_not_name_a_year(client_logged):
    """?scope=all lists every year, so its empty state has no year to name."""
    url = reverse("books:list")
    actual = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert "Įrašų nėra" in actual
    assert "1999" not in actual


# ----------------------------------------------------------------------------
#                                                        Books New/Update View
# ----------------------------------------------------------------------------
def test_view_new_func():
    view = resolve("/books/new/")

    assert views.New == view.func.view_class


def test_view_update_func():
    view = resolve("/books/update/1/")

    assert views.Update == view.func.view_class


@time_machine.travel("2000-01-01")
def test_load_books_form(client_logged):
    url = reverse("books:new")

    response = client_logged.get(url, {})

    actual = response.content.decode()

    assert response.status_code == 200
    assert '<input type="text" name="started" value="1999-01-01"' in actual
    assert url in actual


def test_save_book(client_logged):
    data = {"started": "1999-01-01", "author": "AAA", "title": "TTT"}

    url = reverse("books:new")

    response = client_logged.post(url, data, follow=True)

    assert response.resolver_match.func.view_class is views.Lists

    obj = Book.objects.first()

    assert obj.started == date(1999, 1, 1)
    assert obj.author == "AAA"
    assert obj.title == "TTT"


def test_books_save_invalid_data(client_logged):
    data = {"started": "", "author": "A", "title": "T"}

    url = reverse("books:new")

    response = client_logged.post(url, data)

    actual = response.context["form"]

    assert not actual.is_valid()


def test_books_update(client_logged):
    book = BookFactory()

    data = {
        "started": "1999-01-01",
        "ended": "1999-01-31",
        "author": "AAA",
        "title": "TTT",
    }
    url = reverse("books:update", kwargs={"pk": book.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "1999-01-31" in actual
    assert "AAA" in actual
    assert "TTT" in actual


def test_books_load_update_form(client_logged):
    i = BookFactory()
    url = reverse("books:update", kwargs={"pk": i.pk})

    response = client_logged.get(url, follow=True)
    actual = response.content.decode()

    assert url in actual
    assert "1999-01-01" in actual
    assert "Author" in actual
    assert "Book Title" in actual
    assert "Remark" in actual


def test_book_update_to_another_year(client_logged):
    income = BookFactory()

    data = {
        "started": "1999-12-31",
        "ended": "2010-12-31",
        "author": "Author",
        "title": "Book Title",
        "remark": "Pastaba",
    }
    url = reverse("books:update", kwargs={"pk": income.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


@time_machine.travel("2000-03-03")
def test_books_update_past_record(main_user, client_logged):
    main_user.year = 2000
    i = BookFactory(started=date(1974, 12, 12))

    data = {
        "started": "1999-03-03",
        "author": "XXX",
        "title": "YYY",
        "remark": "ZZZ",
    }
    url = reverse("books:update", kwargs={"pk": i.pk})

    client_logged.post(url, data)

    actual = models.Book.objects.get(pk=i.pk)
    assert actual.started == date(1999, 3, 3)
    assert actual.author == "XXX"
    assert actual.title == "YYY"
    assert actual.remark == "ZZZ"


def test_books_update_not_load_other_user(client_logged, second_user):
    BookFactory()
    obj = BookFactory(author="xxx", title="yyy", user=second_user)

    url = reverse("books:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_book_update_invalid_start_date(client_logged):
    income = BookFactory()

    data = {
        "started": "",
        "ended": "2010-12-31",
        "author": "Author",
        "title": "Book Title",
        "remark": "Pastaba",
    }
    url = reverse("books:update", kwargs={"pk": income.pk})

    response = client_logged.post(url, data)
    actual = response.context["form"]

    assert not actual.is_valid()


# -------------------------------------------------------------------------------------
#                                                                           Book Delete
# -------------------------------------------------------------------------------------
def test_view_books_delete_func():
    view = resolve("/books/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_books_delete_200(client_logged):
    p = BookFactory()

    url = reverse("books:delete", kwargs={"pk": p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_books_delete_load_form(client_logged):
    p = BookFactory()

    url = reverse("books:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url, {}, follow=True)

    actual = response.content.decode("utf-8")

    assert url in actual
    assert '<form method="POST"' in actual
    assert "Ar tikrai norite ištrinti: <strong>Book Title</strong>?" in actual


def test_view_books_delete(client_logged):
    p = BookFactory()

    assert models.Book.objects.all().count() == 1
    url = reverse("books:delete", kwargs={"pk": p.pk})

    client_logged.post(url, {}, follow=True)

    assert models.Book.objects.all().count() == 0


def test_books_delete_other_user_get_form(client_logged, second_user):
    obj = BookFactory(user=second_user)

    url = reverse("books:delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_books_delete_other_user_post_form(client_logged, second_user):
    obj = BookFactory(user=second_user)

    url = reverse("books:delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert models.Book.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                          Books Search
# -------------------------------------------------------------------------------------
def test_search_func():
    view = resolve("/books/search/")

    assert views.Search is view.func.view_class


def test_search_get_200(client_logged):
    url = reverse("books:search")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_not_found(client_logged):
    BookFactory()

    url = reverse("books:search")
    response = client_logged.get(url, {"search": "xxx"})
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual


def test_search_found(client_logged):
    BookFactory()

    url = reverse("books:search")
    response = client_logged.get(url, {"search": "1999 title"})
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Book Title" in actual
    assert "Author" in actual


def test_search_spans_years(client_logged):
    """The year the header selects does not narrow a search."""
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse("books:search")
    actual = client_logged.get(url, {"search": "Old Book"}).content.decode("utf-8")

    assert "Old Book" in actual
    assert "1974-01-01" in actual


def test_search_reset_url_restores_the_year(client_logged):
    """Reset is what ends a search: its url is the selected year's list again."""
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    data = client_logged.get(reverse("books:tab_data")).content.decode("utf-8")
    assert f'hx-get="{reverse("books:list")}"' in data

    actual = client_logged.get(reverse("books:list")).content.decode("utf-8")

    assert "This Year" in actual
    assert "Old Book" not in actual


def test_search_pagination_first_page(client_logged):
    u = UserFactory()
    i = BookFactory.build_batch(51, user=u)
    Book.objects.bulk_create(i)

    url = reverse("books:search")
    response = client_logged.get(url, {"search": "title"})
    actual = response.content.decode("utf-8")

    assert actual.count("Author") == 50


def test_search_pagination_second_page(client_logged):
    u = UserFactory()
    i = BookFactory.build_batch(51, user=u)
    Book.objects.bulk_create(i)

    url = reverse("books:search")

    response = client_logged.get(url, {"page": 2, "search": "author"})
    actual = response.content.decode("utf-8")

    assert actual.count("Author") == 1


# -------------------------------------------------------------------------------------
#                                                                  Target Create/Update
# -------------------------------------------------------------------------------------
def test_target_func():
    view = resolve("/books/target/new/")

    assert views.TargetNew is view.func.view_class


def test_target_200(client_logged):
    url = reverse("books:target_new")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_target_load_form(client_logged):
    url = reverse("books:target_new")

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


def test_target_new(client_logged):
    data = {"year": 1999, "quantity": 66}
    url = reverse("books:target_new")
    client_logged.post(url, data)

    assert models.BookTarget.objects.first().quantity == 66


def test_target_new_invalid_data(client_logged):
    data = {"year": -2, "quantity": "x"}

    url = reverse("books:target_new")

    response = client_logged.post(url, data)

    form = response.context["form"]

    assert not form.is_valid()


def test_target_update(client_logged):
    p = BookTargetFactory()

    data = {"year": 1999, "quantity": 66}
    url = reverse("books:target_update", kwargs={"pk": p.pk})

    client_logged.post(url, data)

    assert models.BookTarget.objects.first().quantity == 66


def test_target_load_update_form(client_logged):
    p = BookTargetFactory()

    data = {"year": 1999, "quantity": 66}
    url = reverse("books:target_update", kwargs={"pk": p.pk})

    response = client_logged.get(url, data)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert '<input type="text" name="year" value="1999"' in actual
