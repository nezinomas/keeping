import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...core.tests.utils import view_for
from ...users.tests.factories import UserFactory
from .. import models, views
from ..forms import BookTargetForm
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
        f'hx-get="{tab.url}" hx-target="#tab_content" hx-trigger="reload from:body"'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode()

    for tab in TABS:
        assert f'hx-get="{tab.url}"' in content


@pytest.mark.parametrize(
    ("url_name", "kwargs", "title"),
    [
        ("books:tab_index", {}, "Knygos | Apžvalga"),
        ("books:tab_data", {"scope": "year"}, "Knygos | Duomenys"),
    ],
    ids=["index", "data"],
)
def test_browser_title_names_the_open_tab(client_logged, url_name, kwargs, title):
    content = client_logged.get(reverse(url_name, kwargs=kwargs)).content.decode()

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


def _page_queries(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


@pytest.mark.parametrize(
    ("url_name", "kwargs"),
    [
        ("books:tab_index", {}),
        ("books:tab_data", {"scope": "year"}),
        ("books:list", {"scope": "year"}),
    ],
    ids=["index", "data", "list"],
)
def test_page_query_count_does_not_grow_with_the_books(client_logged, url_name, kwargs):
    url = reverse(url_name, kwargs=kwargs)
    for _i in range(2):
        BookFactory()
    two = _page_queries(client_logged, url)

    for _i in range(2, 6):
        BookFactory()
    six = _page_queries(client_logged, url)

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


@pytest.mark.parametrize(
    "targets, link_of, no_goal_shown",
    [
        (0, lambda ts: reverse("books:target_new"), True),
        (
            1,
            lambda ts: reverse("books:target_update", kwargs={"pk": ts[0].pk}),
            False,
        ),
    ],
    ids=["target_new", "target_update"],
)
def test_overview_goal_pencil_opens_the_goal_form(
    client_logged, targets, link_of, no_goal_shown
):
    link = link_of(BookTargetFactory.create_batch(targets))

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert content.count(f'hx-get="{link}"') == 1
    assert f'<button type="button" class="trend-card__edit" hx-get="{link}"' in content
    assert re.search(
        rf'trend-card__edit" hx-get="{link}"[^>]*hx-target="#mainModal"', content
    )
    assert 'class="bi bi-pencil"' in content
    assert ("Neįvestas tikslas" in content) is no_goal_shown


def test_data_tab_reads_search_then_table(client_logged):
    url = reverse("books:tab_data", kwargs={"scope": "year"})
    content = client_logged.get(url).content.decode("utf-8")

    assert '<input type="search" name="search"' in content
    assert 'id="id_search"' in content
    assert content.index('id="search-form"') < content.index('id="data"')
    assert 'id="chart-finished-container"' not in content


@pytest.mark.parametrize(
    ("scope", "reloaded"),
    [("all", "all"), ("bogus", "year")],
    ids=["all_records", "junk_reloads_the_year"],
)
def test_data_tab_reloads_its_scope(client_logged, scope, reloaded):
    url = reverse("books:tab_data", kwargs={"scope": scope})
    content = client_logged.get(url).content.decode("utf-8")

    reload_url = reverse("books:tab_data", kwargs={"scope": reloaded})
    assert f'hx-get="{reload_url}" hx-target="#tab_content"' in content


def test_navbar_all_records_opens_the_data_tab_on_every_year(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    url = reverse("books:tab_data", kwargs={"scope": "all"})
    assert f'<a href="{url}">Visi įrašai</a>' in content


@pytest.mark.parametrize(
    "url",
    ["/books/data/", "/books/lists/", "/books/lists/year/"],
    ids=["bare_data", "bare_lists", "lists_with_scope"],
)
def test_the_old_spellings_are_gone(client_logged, url):
    response = client_logged.get(url, {"scope": "all"})

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("url_name", "kwargs", "params", "link_name", "query"),
    [
        ("books:list", {"scope": "all"}, {}, "books:list", "page=2"),
        ("books:tab_data", {"scope": "all"}, {}, "books:list", "page=2"),
        (
            "books:search",
            {},
            {"search": "title & author"},
            "books:search",
            "page=2&search=title%20%26%20author",
        ),
        (
            "books:search",
            {},
            {"search": "title & author", "page": 2},
            "books:search",
            "page=1&search=title%20%26%20author",
        ),
    ],
    ids=["all_records", "data_all_records", "search_encoded", "search_encoded_back"],
)
def test_page_links_keep_their_query(
    client_logged, url_name, kwargs, params, link_name, query
):
    Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    url = reverse(url_name, kwargs=kwargs)
    content = client_logged.get(url, params).content.decode("utf-8")

    link = reverse(link_name, kwargs=kwargs)
    # the other page's number and the next or previous arrow
    assert content.count(f'hx-get="{link}?{query}"') == 2


def test_list_with_data(client_logged):
    BookFactory()

    url = reverse("books:list", kwargs={"scope": "year"})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Author" in actual
    assert "Book Title" in actual
    assert "Remark" in actual


def test_the_number_column_header_is_translated(client_logged):
    BookFactory()

    url = reverse("books:list", kwargs={"scope": "year"})
    actual = client_logged.get(url).content.decode("utf-8")

    assert '<th class="text-left day-col">Nr.</th>' in actual


@pytest.mark.parametrize(
    ("url_name", "kwargs", "params", "shown", "hidden"),
    [
        ("books:tab_data", {"scope": "year"}, {}, ["This Year"], ["Old Book"]),
        ("books:tab_data", {"scope": "all"}, {}, ["This Year", "Old Book"], []),
        ("books:tab_data", {"scope": "bogus"}, {}, ["This Year"], ["Old Book"]),
        ("books:list", {"scope": "year"}, {}, ["This Year"], ["Old Book"]),
        (
            "books:list",
            {"scope": "all"},
            {},
            ["This Year", "Old Book", "1974-01-01"],
            [],
        ),
        ("books:list", {"scope": "bogus"}, {}, ["This Year"], ["Old Book"]),
        ("books:search", {}, {"search": "Old Book"}, ["Old Book", "1974-01-01"], []),
    ],
    ids=["data", "data_all", "data_junk", "list", "list_all", "list_junk", "search"],
)
def test_a_listing_shows_the_books_of_its_scope(
    client_logged, url_name, kwargs, params, shown, hidden
):
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse(url_name, kwargs=kwargs)
    actual = client_logged.get(url, params).content.decode("utf-8")

    for text in shown:
        assert text in actual
    for text in hidden:
        assert text not in actual


@pytest.mark.parametrize(
    ("scope", "shown", "hidden"),
    [
        ("year", ["<b>1999</b> metais įrašų nėra"], []),
        ("all", ["Įrašų nėra"], ["1999"]),
    ],
    ids=["this_year_names_the_year", "all_books_names_no_year"],
)
def test_list_empty_state(client_logged, scope, shown, hidden):
    url = reverse("books:list", kwargs={"scope": scope})
    actual = client_logged.get(url).content.decode("utf-8")

    for text in shown:
        assert text in actual
    for text in hidden:
        assert text not in actual


@time_machine.travel("2000-01-01")
@pytest.mark.parametrize(
    "url_of, expected",
    [
        (
            lambda book: reverse("books:new"),
            ['<input type="text" name="started" value="1999-01-01"'],
        ),
        (
            lambda book: reverse("books:update", kwargs={"pk": book.pk}),
            ["1999-01-01", "Author", "Book Title", "Remark"],
        ),
    ],
    ids=["new", "update"],
)
def test_books_load_form(client_logged, url_of, expected):
    url = url_of(BookFactory())

    actual = client_logged.get(url, {}, follow=True).content.decode()

    assert url in actual
    for text in expected:
        assert text in actual


@pytest.mark.parametrize(
    "url_of",
    [
        lambda: reverse("books:new"),
        lambda: reverse("books:update", kwargs={"pk": BookFactory().pk}),
    ],
    ids=["new", "update"],
)
def test_save_book(client_logged, url_of):
    data = {"started": "1999-01-01", "author": "AAA", "title": "TTT"}

    url = url_of()

    response = client_logged.post(url, data, follow=True)

    assert response.redirect_chain == [
        (reverse("books:list", kwargs={"scope": "year"}), 302)
    ]

    obj = Book.objects.first()

    assert obj.started == date(1999, 1, 1)
    assert obj.author == "AAA"
    assert obj.title == "TTT"


@pytest.mark.parametrize(
    ("url_name", "has_book", "data", "field", "message"),
    [
        (
            "books:new",
            False,
            {"started": "", "author": "A", "title": "T"},
            "started",
            "Šis laukas yra privalomas.",
        ),
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
            "started",
            "Šis laukas yra privalomas.",
        ),
        (
            "books:target_new",
            False,
            {"year": -2, "quantity": "x"},
            "year",
            "Įsitikinkite, kad reikšmė yra didesnė arba lygi 0.",
        ),
    ],
    ids=["book", "book_update", "goal"],
)
def test_an_invalid_post_returns_the_form_with_its_error(
    client_logged, url_name, has_book, data, field, message
):
    kwargs = {}
    if has_book:
        kwargs = {"pk": BookFactory().pk}

    response = client_logged.post(reverse(url_name, kwargs=kwargs), data)

    actual = response.content.decode("utf-8")
    assert re.search(
        rf'name="{field}" value="{data[field]}"[^>]*is-invalid[^>]*>', actual
    )
    assert f'<div class="invalid-feedback">{message}</div>' in actual


@pytest.mark.parametrize(
    ("started", "data", "shown", "hidden"),
    [
        (
            date(1999, 1, 1),
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
            date(1999, 1, 1),
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
        (
            date(1974, 12, 12),
            {
                "started": "1999-03-03",
                "author": "XXX",
                "title": "YYY",
                "remark": "ZZZ",
            },
            ["1999-03-03", "XXX", "YYY"],
            [],
        ),
    ],
    ids=["same_year", "another_year", "past_record"],
)
def test_books_update(client_logged, started, data, shown, hidden):
    book = BookFactory(started=started)
    url = reverse("books:update", kwargs={"pk": book.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")
    for text in shown:
        assert text in actual
    for text in hidden:
        assert text not in actual
    saved = models.Book.objects.get(pk=book.pk)
    assert saved.started == date.fromisoformat(data["started"])
    assert saved.author == data["author"]
    assert saved.title == data["title"]
    assert saved.remark == data.get("remark", "")


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

    for text in expected:
        assert text in actual


@pytest.mark.parametrize(
    ("scope", "reset"),
    [("year", "year"), ("all", "all"), ("bogus", "year")],
    ids=["year", "all_records", "junk_resets_to_the_year"],
)
def test_search_reset_returns_to_the_open_scope(client_logged, scope, reset):
    url = reverse("books:tab_data", kwargs={"scope": scope})
    data = client_logged.get(url).content.decode("utf-8")

    reset_url = reverse("books:list", kwargs={"scope": reset})
    assert re.search(rf'<button[^>]*hx-get="{reset_url}"', data)


@pytest.mark.parametrize(
    ("name", "kwargs", "params", "expected", "first_numbers"),
    [
        ("books:search", {}, {"search": "title"}, 50, ["1"]),
        ("books:search", {}, {"page": 2, "search": "author"}, 1, ["1"]),
        ("books:search", {}, {"page": "x", "search": "title"}, 50, ["1"]),
        ("books:search", {}, {"page": 0, "search": "title"}, 50, ["1"]),
        ("books:search", {}, {"page": -3, "search": "title"}, 50, ["1"]),
        ("books:search", {}, {"page": 10**30, "search": "title"}, 0, []),
        ("books:list", {"scope": "all"}, {}, 50, ["51"]),
        ("books:list", {"scope": "all"}, {"page": 2}, 1, ["1"]),
        ("books:list", {"scope": "all"}, {"page": "x"}, 50, ["51"]),
        ("books:list", {"scope": "all"}, {"page": 0}, 50, ["51"]),
        ("books:list", {"scope": "all"}, {"page": -3}, 50, ["51"]),
        ("books:list", {"scope": "all"}, {"page": 999}, 0, []),
        ("books:list", {"scope": "all"}, {"page": 10**30}, 0, []),
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
def test_pagination(client_logged, name, kwargs, params, expected, first_numbers):
    Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    response = client_logged.get(reverse(name, kwargs=kwargs), params)
    actual = response.content.decode("utf-8")

    assert actual.count("Author") == expected
    numbers = re.findall(r'<td class="text-left">(\d+)</td>', actual)
    assert numbers[:1] == first_numbers


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabIndex).get_context_data(), id="index"
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.Lists, scope="year").get_queryset(),
            id="list",
        ),
        pytest.param(
            lambda rf, u: BookTargetForm(user=u, today=date(2000, 2, 2)),
            id="goal_form",
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, call):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)


def _new_goal_url():
    return reverse("books:target_new")


def _update_goal_url():
    return reverse("books:target_update", kwargs={"pk": BookTargetFactory().pk})


GOAL_URL = pytest.mark.parametrize(
    "make_url", [_new_goal_url, _update_goal_url], ids=["new", "update"]
)


@GOAL_URL
def test_target_load_form(client_logged, make_url):
    url = make_url()

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


@GOAL_URL
def test_target_save(client_logged, make_url):
    url = make_url()

    client_logged.post(url, {"year": 1999, "quantity": 66})

    assert models.BookTarget.objects.first().quantity == 66


@GOAL_URL
def test_a_saved_goal_triggers_reload(client_logged, make_url):
    response = client_logged.post(
        make_url(), {"year": 1999, "quantity": 66}, headers={"HX-Request": "true"}
    )

    assert response.headers["HX-Trigger"] == '{"reload": {}}'
