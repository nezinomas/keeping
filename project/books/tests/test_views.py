import json
import re
from datetime import date

import pytest
from django.urls import reverse

from ...core.tests.utils import (
    count_queries,
    form_posts_to,
    nav_tabs,
    quick_add_pills,
    stat_card_edit_urls,
    stat_cards,
    view_for,
)
from ...users.tests.factories import UserFactory
from .. import models, views
from ..forms import BookTargetForm
from .factories import BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


def test_a_plain_visit_returns_the_whole_paper_page(client_logged):
    content = client_logged.get(reverse("books:tab_index")).content.decode("utf-8")

    assert '<nav class="subnav">' in content
    assert re.search(r'<link[^>]*href="[^"]*css/paper\.min\.css[^"]*"', content)
    assert not re.search(r"<link[^>]*css/main\.min\.css", content)
    assert '<div class="paper-skin"' in content


@pytest.mark.parametrize(
    ("url_name", "kwargs", "reloaded_kwargs"),
    [
        ("books:tab_index", {}, {}),
        ("books:tab_data", {"scope": "all"}, {"scope": "all"}),
        ("books:tab_data", {"scope": "bogus"}, {"scope": "year"}),
    ],
    ids=["index", "data_all", "data_junk_reloads_the_year"],
)
def test_only_the_open_tab_reloads_on_a_saved_book_or_goal(
    client_logged, url_name, kwargs, reloaded_kwargs
):
    url = reverse(url_name, kwargs=kwargs)
    content = client_logged.get(url, headers={"HX-Request": "true"}).content.decode(
        "utf-8"
    )

    reload_url = reverse(url_name, kwargs=reloaded_kwargs)
    listener = (
        f'<div hx-get="{reload_url}" hx-target="#tab_content" '
        'hx-trigger="reload from:body"></div>'
    )
    assert listener in content
    assert content.count("reload from:body") == 1


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert nav_tabs(content) == [
        ("index", reverse("books:tab_index")),
        ("data", reverse("books:tab_data", kwargs={"scope": "year"})),
    ]


def test_nav_selects_the_open_tab(client_logged):
    url = reverse("books:tab_data", kwargs={"scope": "year"})
    content = client_logged.get(url).content.decode("utf-8")

    assert re.findall(r'id="tab-(\w+)"[^>]*aria-selected="true"', content) == ["data"]


def test_browser_title_names_the_open_tab(client_logged):
    url = reverse("books:tab_data", kwargs={"scope": "year"})
    content = client_logged.get(url).content.decode("utf-8")

    assert "<title>Knygos | Duomenys</title>" in content


@pytest.mark.parametrize(
    "pattern",
    [
        pytest.param('<h1 class="visually-hidden">Knygos</h1>', id="heading"),
        pytest.param(r'<script[^>]*src="[^"]*js/chart_paper\.js"', id="chart_theme"),
        pytest.param(
            '<h2 class="panel__title">Perskaitytos knygos</h2>', id="finished_panel"
        ),
    ],
)
def test_books_index_shows_its_heading_chart_theme_and_finished_panel(
    client_logged, pattern
):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert re.search(pattern, content)


def test_books_adds_a_book_from_the_foot_of_the_page(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert '<div class="quick-add"' in content
    assert quick_add_pills(content) == [
        ("button", "", f'hx-get="{reverse("books:new")}"', "Pridėti knygą")
    ]


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
    BookFactory()
    BookFactory(ended=date(1999, 2, 1))
    two = count_queries(lambda: client_logged.get(url))

    BookFactory()
    BookFactory(ended=date(1999, 3, 1))
    for year in (1997, 1998):
        BookFactory(started=date(year, 1, 1), ended=date(year, 2, 1))
    six = count_queries(lambda: client_logged.get(url))

    assert six == two


# a Book table row's author, title, remark, started and ended cells
ROW = re.compile(
    r'<td class="text-left">([^<]*)</td>\s*'
    r'<td class="text-left">„([^<]*)”</td>\s*'
    r'<td class="text-left">([^<]*)</td>\s*'
    r'<td class="text-center date-col">([^<]*)</td>\s*'
    r'<td class="text-center date-col">([^<]*)</td>'
)
THIS_YEAR = ("Author", "This Year", "Remark", "1999-01-01", "-")
OLD_BOOK = ("Author", "Old Book", "Remark", "1974-01-01", "1974-01-31")


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
    BookTargetFactory(year=1999, quantity=5)

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    carried = re.search(
        r'<script id="chart-finished-data" type="application/json">(.*?)</script>',
        content,
    )
    assert json.loads(carried[1]) == {
        "categories": [1999],
        "data": [{"y": 1, "target": 5}],
        "targets": [5],
    }


@pytest.mark.parametrize(
    ("open_books", "finished_books", "goals", "expected"),
    [
        (
            2,
            1,
            1,
            [("Perskaitytos", "1", ""), ("Skaitomos", "2", ""), ("Tikslas", "5", "")],
        ),
        (
            0,
            0,
            0,
            [
                ("Perskaitytos", "0", ""),
                ("Skaitomos", "0", ""),
                ("Tikslas", "&mdash;", "Neįvestas tikslas"),
            ],
        ),
    ],
    ids=["cards", "cards_no_data"],
)
def test_overview_cards(client_logged, open_books, finished_books, goals, expected):
    BookFactory.create_batch(open_books)
    BookFactory.create_batch(finished_books, ended=date(1999, 2, 1))
    BookTargetFactory.create_batch(goals, quantity=5)

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert stat_cards(content) == expected


def _new_goal_url():
    return reverse("books:target_new")


def _update_goal_url():
    return reverse("books:target_update", kwargs={"pk": BookTargetFactory().pk})


GOAL_URL = pytest.mark.parametrize(
    "make_url", [_new_goal_url, _update_goal_url], ids=["new", "update"]
)


@GOAL_URL
def test_overview_goal_pencil_opens_the_goal_form(client_logged, make_url):
    link = make_url()

    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert stat_card_edit_urls(content) == [link]


def test_data_tab_reads_search_then_table(client_logged):
    url = reverse("books:tab_data", kwargs={"scope": "year"})
    content = client_logged.get(url).content.decode("utf-8")

    assert re.search(r'<input type="search" name="search"\s+id="id_search"', content)
    assert content.index('id="search-form"') < content.index('id="data"')
    assert 'id="chart-finished-container"' not in content


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
    ("url_name", "kwargs", "params", "link_name", "link_kwargs", "query"),
    [
        ("books:list", {"scope": "all"}, {}, "books:list", {"scope": "all"}, "page=2"),
        (
            "books:list",
            {"scope": "bogus"},
            {},
            "books:list",
            {"scope": "year"},
            "page=2",
        ),
        (
            "books:tab_data",
            {"scope": "all"},
            {},
            "books:list",
            {"scope": "all"},
            "page=2",
        ),
        (
            "books:search",
            {},
            {"search": "title & author"},
            "books:search",
            {},
            "page=2&search=title%20%26%20author",
        ),
        (
            "books:search",
            {},
            {"search": "title & author", "page": 2},
            "books:search",
            {},
            "page=1&search=title%20%26%20author",
        ),
    ],
    ids=[
        "all_records",
        "list_junk",
        "data_all_records",
        "search_encoded",
        "search_encoded_back",
    ],
)
def test_page_links_keep_their_query(
    client_logged, url_name, kwargs, params, link_name, link_kwargs, query
):
    models.Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    url = reverse(url_name, kwargs=kwargs)
    content = client_logged.get(url, params).content.decode("utf-8")

    link = reverse(link_name, kwargs=link_kwargs)
    # the other page's number and the next or previous arrow
    page_link = (
        rf'<a role="button"[^>]*hx-get="{re.escape(f"{link}?{query}")}"'
        r'[^>]* hx-target="#data"'
    )
    assert len(re.findall(page_link, content)) == 2


def test_the_number_column_header_is_translated(client_logged):
    BookFactory()

    url = reverse("books:list", kwargs={"scope": "year"})
    actual = client_logged.get(url).content.decode("utf-8")

    assert '<th class="text-left day-col">Nr.</th>' in actual


@pytest.mark.parametrize(
    ("url_name", "kwargs", "params", "rows"),
    [
        ("books:list", {"scope": "year"}, {}, [THIS_YEAR]),
        ("books:list", {"scope": "all"}, {}, [THIS_YEAR, OLD_BOOK]),
        ("books:list", {"scope": "bogus"}, {}, [THIS_YEAR]),
        ("books:search", {}, {"search": "Old Book"}, [OLD_BOOK]),
    ],
    ids=["list", "list_all", "list_junk", "search"],
)
def test_a_listing_shows_the_books_of_its_scope(
    client_logged, url_name, kwargs, params, rows
):
    BookFactory(title="This Year")
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse(url_name, kwargs=kwargs)
    actual = client_logged.get(url, params).content.decode("utf-8")

    assert ROW.findall(actual) == rows


def test_a_book_row_opens_its_own_forms(client_logged):
    book = BookFactory()

    url = reverse("books:list", kwargs={"scope": "year"})
    actual = client_logged.get(url).content.decode("utf-8")

    rows = re.findall(
        r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"'
        r'.*?<td class="edit-col">\s*<a role="button" hx-get="([^"]*)"'
        r'.*?<td class="delete-col">\s*<a role="button" hx-get="([^"]*)"',
        actual,
        re.DOTALL,
    )
    update = f"/books/update/{book.pk}/"
    assert rows == [(update, update, f"/books/delete/{book.pk}/")]


@pytest.mark.parametrize(
    ("ended", "row_class"),
    [(None, "currently-reading-book"), (date(1999, 1, 31), "")],
    ids=["open_book_is_marked", "finished_book_is_not"],
)
def test_a_book_row_marks_a_book_still_being_read(client_logged, ended, row_class):
    BookFactory(ended=ended)

    url = reverse("books:list", kwargs={"scope": "year"})
    actual = client_logged.get(url).content.decode("utf-8")

    assert re.findall(r'<tr hx-get="[^"]*"[^>]* class="([^"]*)">', actual) == [
        row_class
    ]


@pytest.mark.parametrize(
    ("scope", "notice"),
    [
        ("year", "<b>1999</b> metais įrašų nėra."),
        ("all", "Įrašų nėra"),
    ],
    ids=["this_year_names_the_year", "all_books_names_no_year"],
)
def test_list_empty_state(client_logged, scope, notice):
    url = reverse("books:list", kwargs={"scope": scope})
    actual = client_logged.get(url).content.decode("utf-8")

    assert re.fullmatch(
        rf'\s*<div class="alert">\s*{re.escape(notice)}\s*</div>\s*',
        actual,
    )


def _new_book_url():
    return reverse("books:new")


def _update_book_url():
    return reverse("books:update", kwargs={"pk": BookFactory().pk})


def _delete_book_url():
    return reverse("books:delete", kwargs={"pk": BookFactory().pk})


@pytest.mark.parametrize(
    "make_url, form_id, expected",
    [
        (_new_book_url, "generic-form", []),
        (
            _update_book_url,
            "generic-form",
            [
                '<input type="text" name="started" value="1999-01-01"',
                '<input type="text" name="author" value="Author"',
                '<input type="text" name="title" value="Book Title"',
                r'<textarea name="remark"[^>]*>\s*Remark</textarea>',
            ],
        ),
        (
            _delete_book_url,
            "delete-form",
            [r"Ar tikrai norite ištrinti: <strong>Book Title</strong>\?"],
        ),
    ],
    ids=["new", "update", "delete"],
)
def test_books_load_form(client_logged, make_url, form_id, expected):
    url = make_url()

    actual = client_logged.get(url).content.decode("utf-8")

    assert form_posts_to(actual, form_id, url)
    assert [pattern for pattern in expected if not re.search(pattern, actual)] == []


def test_save_book(client_logged):
    data = {"started": "1999-01-01", "author": "AAA", "title": "TTT"}

    response = client_logged.post(reverse("books:new"), data, follow=True)

    assert response.redirect_chain == [
        (reverse("books:list", kwargs={"scope": "year"}), 302)
    ]

    assert list(models.Book.objects.values_list("started", "author", "title")) == [
        (date(1999, 1, 1), "AAA", "TTT")
    ]


@pytest.mark.parametrize(
    ("make_url", "data", "field", "message"),
    [
        (
            _new_book_url,
            {"started": "", "author": "A", "title": "T"},
            "started",
            "Šis laukas yra privalomas.",
        ),
        (
            _update_book_url,
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
            _new_goal_url,
            {"year": -2, "quantity": "x"},
            "year",
            "Įsitikinkite, kad reikšmė yra didesnė arba lygi 0.",
        ),
    ],
    ids=["book", "book_update", "goal"],
)
def test_an_invalid_post_returns_the_form_with_its_error(
    client_logged, make_url, data, field, message
):
    response = client_logged.post(make_url(), data)

    actual = response.content.decode("utf-8")
    assert re.search(
        rf'name="{field}" value="{data[field]}"[^>]*is-invalid[^>]*>', actual
    )
    assert f'<div class="invalid-feedback">{message}</div>' in actual


@pytest.mark.parametrize(
    ("started", "data", "rows", "saved"),
    [
        (
            date(1999, 1, 1),
            {
                "started": "1999-01-01",
                "ended": "1999-01-31",
                "author": "AAA",
                "title": "TTT",
            },
            [("AAA", "TTT", "", "1999-01-01", "1999-01-31")],
            (date(1999, 1, 1), date(1999, 1, 31), "AAA", "TTT", ""),
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
            (date(1999, 12, 31), date(2010, 12, 31), "Author", "Book Title", "Pastaba"),
        ),
        (
            date(1974, 12, 12),
            {
                "started": "1999-03-03",
                "author": "XXX",
                "title": "YYY",
                "remark": "ZZZ",
            },
            [("XXX", "YYY", "ZZZ", "1999-03-03", "-")],
            (date(1999, 3, 3), None, "XXX", "YYY", "ZZZ"),
        ),
    ],
    ids=["same_year", "another_year", "past_record"],
)
def test_books_update(client_logged, started, data, rows, saved):
    book = BookFactory(started=started)
    url = reverse("books:update", kwargs={"pk": book.pk})

    response = client_logged.post(url, data, follow=True)

    assert ROW.findall(response.content.decode("utf-8")) == rows
    assert (
        models.Book.objects.filter(pk=book.pk)
        .values_list("started", "ended", "author", "title", "remark")
        .get()
    ) == saved


@pytest.mark.parametrize(
    "url_name", ["books:update", "books:delete"], ids=["update", "delete"]
)
def test_books_form_of_another_users_book_is_not_found(
    client_logged, second_user, url_name
):
    obj = BookFactory(author="xxx", title="yyy", user=second_user)

    response = client_logged.get(reverse(url_name, kwargs={"pk": obj.pk}))

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("deleted", "remaining"),
    [("Mine", ["Kept", "Theirs"]), ("Theirs", ["Kept", "Mine", "Theirs"])],
    ids=["own_book", "other_user"],
)
def test_books_delete(client_logged, second_user, deleted, remaining):
    books = {
        "Mine": BookFactory(title="Mine"),
        "Kept": BookFactory(title="Kept"),
        "Theirs": BookFactory(title="Theirs", user=second_user),
    }
    url = reverse("books:delete", kwargs={"pk": books[deleted].pk})

    client_logged.post(url, {}, follow=True)

    titles = models.Book.objects.order_by("title").values_list("title", flat=True)
    assert list(titles) == remaining


@pytest.mark.parametrize(
    ("search", "rows", "notices"),
    [
        ("xxx", [], 1),
        ("1999 title", [("Author", "Book Title", "Remark", "1999-01-01", "-")], 0),
    ],
    ids=["not_found", "found"],
)
def test_search(client_logged, search, rows, notices):
    BookFactory()

    url = reverse("books:search")
    response = client_logged.get(url, {"search": search})
    actual = response.content.decode("utf-8")

    assert ROW.findall(actual) == rows
    notice = r'<div class="alert">\s*Nieko nerasta\s*</div>'
    assert len(re.findall(notice, actual)) == notices


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
        ("books:list", {"scope": "all"}, {}, 50, ["51"]),
        ("books:list", {"scope": "all"}, {"page": 2}, 1, ["1"]),
        ("books:list", {"scope": "all"}, {"page": 10**30}, 0, []),
    ],
    ids=[
        "search_first_page",
        "search_second_page",
        "list_first_page",
        "list_second_page",
        "list_page_past_any_offset",
    ],
)
def test_pagination(client_logged, name, kwargs, params, expected, first_numbers):
    models.Book.objects.bulk_create(BookFactory.build_batch(51, user=UserFactory()))

    response = client_logged.get(reverse(name, kwargs=kwargs), params)
    actual = response.content.decode("utf-8")

    assert len(ROW.findall(actual)) == expected
    numbers = re.findall(r'<td class="text-left main__figure">(\d+)</td>', actual)
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


@GOAL_URL
def test_goal_load_form(client_logged, make_url):
    url = make_url()

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert form_posts_to(actual, "generic-form", url)
    assert '<input type="text" name="year" value="1999"' in actual


@GOAL_URL
def test_goal_save(client_logged, main_user, make_url):
    url = make_url()

    client_logged.post(url, {"year": 1999, "quantity": 66})

    saved = models.BookTarget.objects.values_list("user", "year", "quantity")
    assert list(saved) == [(main_user.pk, 1999, 66)]


@GOAL_URL
def test_a_saved_goal_triggers_reload(client_logged, make_url):
    response = client_logged.post(
        make_url(), {"year": 1999, "quantity": 66}, headers={"HX-Request": "true"}
    )

    assert response.headers["HX-Trigger"] == '{"reload": {}}'
