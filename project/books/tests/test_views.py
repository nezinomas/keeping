import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...users.tests.factories import UserFactory
from .. import models
from ..tabs import TABS
from .factories import Book, BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


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
    ("url_name", "title"),
    [
        ("books:tab_index", "Knygos | Apžvalga"),
        ("books:tab_data", "Knygos | Duomenys"),
    ],
    ids=["index", "data"],
)
def test_browser_title_names_the_open_tab(client_logged, url_name, title):
    content = client_logged.get(reverse(url_name)).content.decode()

    assert f"<title>{title}</title>" in content


@pytest.mark.parametrize(
    "markup",
    [
        pytest.param('<h1 class="visually-hidden">Knygos</h1>', id="heading"),
        pytest.param("js/chart_paper.js", id="chart_theme"),
        pytest.param(
            '<h2 class="panel__title">Perskaitytos knygos</h2>', id="finished_panel"
        ),
    ],
)
def test_books_index_shows_its_heading_chart_theme_and_finished_panel(
    client_logged, markup
):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert markup in content


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_books_adds_a_book_from_the_foot_of_every_tab(client_logged, tab):
    content = client_logged.get(tab.url).content.decode("utf-8")

    link = reverse("books:new")

    assert 'class="quick-add"' in content
    assert f'class="quick-add__pill" hx-get="{link}"' in content
    assert 'hx-target="#mainModal"' in content
    assert "Pridėti knygą" in content


def _page_queries(client, url_name):
    with CaptureQueriesContext(connection) as queries:
        client.get(reverse(url_name))
    return len(queries)


@pytest.mark.parametrize(
    "url_name",
    ["books:tab_index", "books:tab_data", "books:list"],
    ids=["index", "data", "list"],
)
def test_page_query_count_does_not_grow_with_the_books(client_logged, url_name):
    for _i in range(2):
        BookFactory()
    two = _page_queries(client_logged, url_name)

    for _i in range(2, 6):
        BookFactory()
    six = _page_queries(client_logged, url_name)

    assert six == two


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


def test_overview_carries_the_chart_data(client_logged):
    BookFactory(ended=date(1999, 1, 1))

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert '<script id="chart-finished-data" type="application/json">' in content


@time_machine.travel("1999-07-18")
@pytest.mark.parametrize(
    ("open_books", "finished_books", "expected"),
    [
        (2, 1, [("Perskaitytos", "1"), ("Skaitomos", "2")]),
        (0, 0, [("Perskaitytos", "0"), ("Skaitomos", "0")]),
    ],
    ids=["cards", "cards_no_data"],
)
def test_overview_cards(client_logged, open_books, finished_books, expected):
    BookFactory.create_batch(open_books)
    BookFactory.create_batch(finished_books, ended=date(1999, 2, 1))

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert content.count('class="trend-card"') == 3
    assert re.findall(CARD, content)[:2] == expected


def test_overview_goal_pencil_opens_target_new(client_logged):
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


def test_data_tab_reads_search_then_table(client_logged):
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


def test_list_with_data(client_logged):
    BookFactory()

    url = reverse("books:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Author" in actual
    assert "Book Title" in actual
    assert "Remark" in actual


@pytest.mark.parametrize(
    ("params", "expected"),
    [({}, ["This Year"]), ({"scope": "all"}, ["This Year", "Old Book"])],
    ids=["only_current_year", "all_books"],
)
def test_list_scope_picks_the_books(client_logged, params, expected):
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    content = client_logged.get(reverse("books:list"), params).content.decode()

    assert [t for t in ("This Year", "Old Book") if t in content] == expected


@pytest.mark.parametrize(
    ("url_name", "params"),
    [
        ("books:list", {"scope": "all"}),
        ("books:search", {"search": "Old Book"}),
    ],
    ids=["list_all", "search"],
)
def test_a_listing_that_spans_years_shows_an_old_book(client_logged, url_name, params):
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    actual = client_logged.get(reverse(url_name), params).content.decode("utf-8")

    assert "Old Book" in actual
    assert "1974-01-01" in actual


def test_list_empty_state_names_the_year(client_logged):
    url = reverse("books:list")
    actual = client_logged.get(url).content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra" in actual


def test_list_all_books_empty_state_does_not_name_a_year(client_logged):
    url = reverse("books:list")
    actual = client_logged.get(url, {"scope": "all"}).content.decode("utf-8")

    assert "Įrašų nėra" in actual
    assert "1999" not in actual


@time_machine.travel("2000-01-01")
def test_load_books_form(client_logged):
    url = reverse("books:new")

    response = client_logged.get(url, {})

    actual = response.content.decode()

    assert '<input type="text" name="started" value="1999-01-01"' in actual
    assert url in actual


def test_save_book(client_logged):
    data = {"started": "1999-01-01", "author": "AAA", "title": "TTT"}

    url = reverse("books:new")

    response = client_logged.post(url, data, follow=True)

    assert response.redirect_chain == [(reverse("books:list"), 302)]

    obj = Book.objects.first()

    assert obj.started == date(1999, 1, 1)
    assert obj.author == "AAA"
    assert obj.title == "TTT"


@pytest.mark.parametrize(
    ("url_name", "has_book", "data"),
    [
        ("books:new", False, {"started": "", "author": "A", "title": "T"}),
        (
            "books:update",
            True,
            {
                "started": "",
                "ended": "2010-12-31",
                "author": "Author",
                "title": "Book Title",
                "remark": "Pastaba",
            },
        ),
        ("books:target_new", False, {"year": -2, "quantity": "x"}),
    ],
    ids=["book", "book_update", "goal"],
)
def test_an_invalid_post_returns_the_form_invalid(
    client_logged, url_name, has_book, data
):
    kwargs = {}
    if has_book:
        kwargs = {"pk": BookFactory().pk}

    response = client_logged.post(reverse(url_name, kwargs=kwargs), data)

    assert not response.context["form"].is_valid()


@pytest.mark.parametrize(
    ("data", "shown", "hidden"),
    [
        (
            {
                "started": "1999-01-01",
                "ended": "1999-01-31",
                "author": "AAA",
                "title": "TTT",
            },
            ["1999-01-01", "1999-01-31", "AAA", "TTT"],
            [],
        ),
        (
            {
                "started": "1999-12-31",
                "ended": "2010-12-31",
                "author": "Author",
                "title": "Book Title",
                "remark": "Pastaba",
            },
            [],
            ["2010-12-31"],
        ),
    ],
    ids=["same_year", "another_year"],
)
def test_books_update(client_logged, data, shown, hidden):
    book = BookFactory()
    url = reverse("books:update", kwargs={"pk": book.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")
    assert all(text in actual for text in shown)
    assert not any(text in actual for text in hidden)


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


@pytest.mark.parametrize(
    "url_name", ["books:update", "books:delete"], ids=["update", "delete"]
)
def test_books_form_of_another_users_book_is_not_found(
    client_logged, second_user, url_name
):
    BookFactory()
    obj = BookFactory(author="xxx", title="yyy", user=second_user)

    response = client_logged.get(reverse(url_name, kwargs={"pk": obj.pk}))

    assert response.status_code == 404


def test_view_books_delete_load_form(client_logged):
    p = BookFactory()

    url = reverse("books:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url, {}, follow=True)

    actual = response.content.decode("utf-8")

    assert url in actual
    assert '<form method="POST"' in actual
    assert "Ar tikrai norite ištrinti: <strong>Book Title</strong>?" in actual


@pytest.mark.parametrize(
    ("owned", "remaining"), [(True, 0), (False, 1)], ids=["own_book", "other_user"]
)
def test_books_delete(client_logged, second_user, owned, remaining):
    book = BookFactory() if owned else BookFactory(user=second_user)

    assert models.Book.objects.all().count() == 1
    url = reverse("books:delete", kwargs={"pk": book.pk})

    client_logged.post(url, {}, follow=True)

    assert models.Book.objects.all().count() == remaining


@pytest.mark.parametrize(
    ("search", "expected"),
    [
        ("xxx", ["Nieko nerasta"]),
        ("1999 title", ["1999-01-01", "Book Title", "Author"]),
    ],
    ids=["not_found", "found"],
)
def test_search(client_logged, search, expected):
    BookFactory()

    url = reverse("books:search")
    response = client_logged.get(url, {"search": search})
    actual = response.content.decode("utf-8")

    assert all(text in actual for text in expected)


def test_search_reset_url_restores_the_year(client_logged):
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    data = client_logged.get(reverse("books:tab_data")).content.decode("utf-8")
    assert f'hx-get="{reverse("books:list")}"' in data

    actual = client_logged.get(reverse("books:list")).content.decode("utf-8")

    assert "This Year" in actual
    assert "Old Book" not in actual


@pytest.mark.parametrize(
    ("name", "params", "expected", "first_numbers"),
    [
        ("books:search", {"search": "title"}, 50, ["1"]),
        ("books:search", {"page": 2, "search": "author"}, 1, ["1"]),
        ("books:search", {"page": "x", "search": "title"}, 50, ["1"]),
        ("books:search", {"page": 0, "search": "title"}, 50, ["1"]),
        ("books:search", {"page": -3, "search": "title"}, 50, ["1"]),
        ("books:search", {"page": 10**30, "search": "title"}, 0, []),
        ("books:list", {"scope": "all"}, 50, ["51"]),
        ("books:list", {"scope": "all", "page": 2}, 1, ["1"]),
        ("books:list", {"scope": "all", "page": "x"}, 50, ["51"]),
        ("books:list", {"scope": "all", "page": 0}, 50, ["51"]),
        ("books:list", {"scope": "all", "page": -3}, 50, ["51"]),
        ("books:list", {"scope": "all", "page": 999}, 0, []),
        ("books:list", {"scope": "all", "page": 10**30}, 0, []),
    ],
    ids=[
        "search_first_page",
        "search_second_page",
        "search_page_x",
        "search_page_0",
        "search_page_minus_3",
        "search_page_past_any_offset",
        "list_first_page",
        "list_second_page",
        "list_page_x",
        "list_page_0",
        "list_page_minus_3",
        "list_page_past_the_end",
        "list_page_past_any_offset",
    ],
)
def test_pagination(client_logged, name, params, expected, first_numbers):
    Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    response = client_logged.get(reverse(name), params)
    actual = response.content.decode("utf-8")

    assert actual.count("Author") == expected
    numbers = re.findall(r'<td class="text-left">(\d+)</td>', actual)
    assert numbers[:1] == first_numbers


@pytest.mark.parametrize("name", ["books:index", "books:list"])
def test_a_user_with_no_reading_year_raises(client_logged, main_user, name):
    main_user.year = None
    main_user.save()

    with pytest.raises(ValueError, match="has no year"):
        client_logged.get(reverse(name))


@pytest.mark.parametrize("update", [False, True], ids=["new", "update"])
def test_target_load_form(client_logged, update):
    url = reverse("books:target_new")
    if update:
        url = reverse("books:target_update", kwargs={"pk": BookTargetFactory().pk})

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


@pytest.mark.parametrize("update", [False, True], ids=["new", "update"])
def test_target_save(client_logged, update):
    url = reverse("books:target_new")
    if update:
        url = reverse("books:target_update", kwargs={"pk": BookTargetFactory().pk})

    client_logged.post(url, {"year": 1999, "quantity": 66})

    assert models.BookTarget.objects.first().quantity == 66
