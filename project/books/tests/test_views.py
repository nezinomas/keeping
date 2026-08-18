import re
from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse
from django.utils.translation import gettext as _

from ...users.tests.factories import UserFactory
from .. import models, views
from .factories import Book, BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                             Books Index View
# ----------------------------------------------------------------------------
def test_index_func():
    view = resolve("/books/")

    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse("books:index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_books_index_names_itself_in_the_browser_title(client_logged):
    content = client_logged.get(reverse("books:index")).content.decode("utf-8")

    assert f"<title>{_('Books')}</title>" in content


def test_books_index_wears_the_paper_bundle(client_logged):
    url = reverse("books:index")
    content = client_logged.get(url).content.decode("utf-8")

    assert "css/paper.min.css" in content
    assert "css/main.min.css" not in content
    assert 'class="paper-skin"' in content


def test_books_index_loads_the_paper_chart_theme(client_logged):
    """The chart wears the skin because this page pulls the theme in."""
    url = reverse("books:index")
    content = client_logged.get(url).content.decode("utf-8")

    assert "js/chart_paper.js" in content


def test_books_index_goal_is_edited_from_its_card(client_logged):
    """The pencil in the Goal card is the page's only way into the goal form."""
    url = reverse("books:index")
    content = client_logged.get(url).content.decode("utf-8")

    link = reverse("books:target_new")

    assert content.count(f'hx-get="{link}"') == 1
    assert f'class="trend-card__edit" hx-get="{link}"' in content


def test_books_index_adds_a_book_from_the_foot_of_the_page(client_logged):
    """Both header buttons went with the info row, so this is the only way in."""
    url = reverse("books:index")
    content = client_logged.get(url).content.decode("utf-8")

    link = reverse("books:new")

    assert 'class="quick-add"' in content
    assert f'class="quick-add__pill" hx-get="{link}"' in content
    assert 'hx-target="#mainModal"' in content
    assert "Pridėti knygą" in content


def test_books_index_search_form(client_logged):
    url = reverse("books:index")
    response = client_logged.get(url).content.decode("utf-8")

    assert '<input type="search" name="search"' in response
    assert 'id="id_search"' in response


def test_books_index_reads_cards_chart_search_table(client_logged):
    """The table is the variable-height thing, so nothing goes under it."""
    url = reverse("books:index")
    content = client_logged.get(url).content.decode("utf-8")

    order = [
        content.index('class="stat-cards"'),
        content.index('id="chart-finished-container"'),
        content.index('id="search-form"'),
        content.index('id="data"'),
    ]

    assert order == sorted(order)


def test_books_index_context(client_logged):
    url = reverse("books:index")
    response = client_logged.get(url)

    assert "year" in response.context
    assert "tab" in response.context
    assert "books" in response.context
    assert "cards" in response.context


# ----------------------------------------------------------------------------
#                                                                        Cards
# ----------------------------------------------------------------------------
CARD = re.compile(
    r'trend-card__label">(.*?)</div>\s*<div class="trend-card__value[^"]*">(.*?)</div>',
    re.S,
)


def test_cards_func():
    view = resolve("/books/cards/")

    assert views.Cards == view.func.view_class


def test_cards_200(client_logged):
    url = reverse("books:cards")
    response = client_logged.get(url)

    assert response.status_code == 200


@time_machine.travel("1999-07-18")
def test_cards_html(client_logged):
    BookFactory()
    BookFactory()
    BookFactory(ended=date(1999, 2, 1))

    url = reverse("books:cards")
    content = client_logged.get(url).content.decode("utf-8")

    assert content.count('class="trend-card"') == 3
    assert re.findall(CARD, content)[:2] == [("Perskaitytos", "1"), ("Skaitomos", "2")]


@time_machine.travel("1999-07-18")
def test_cards_no_data(client_logged):
    url = reverse("books:cards")
    content = client_logged.get(url).content.decode("utf-8")

    assert re.findall(CARD, content)[:2] == [("Perskaitytos", "0"), ("Skaitomos", "0")]


def test_cards_goal_pencil_opens_target_new(client_logged):
    url = reverse("books:cards")
    content = client_logged.get(url).content.decode("utf-8")

    link = reverse("books:target_new")

    assert f'<button type="button" class="trend-card__edit" hx-get="{link}"' in content
    assert 'hx-target="#mainModal"' in content
    assert 'class="bi bi-pencil"' in content
    assert "Neįvestas tikslas" in content


def test_cards_goal_pencil_opens_target_update(client_logged):
    t = BookTargetFactory()

    url = reverse("books:cards")
    content = client_logged.get(url).content.decode("utf-8")

    link = reverse("books:target_update", kwargs={"pk": t.pk})

    assert f'<button type="button" class="trend-card__edit" hx-get="{link}"' in content
    assert "Neįvestas tikslas" not in content


# ----------------------------------------------------------------------------
#                                                               Finished Books
# ----------------------------------------------------------------------------
def test_chart_finished_func():
    view = resolve("/books/chart_finished/")

    assert views.ChartFinished == view.func.view_class


def test_chart_finished_200(client_logged):
    url = reverse("books:chart_finished")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_books_index_chart_year(client_logged):
    BookFactory(ended=date(1999, 1, 1))

    url = reverse("books:chart_finished")
    response = client_logged.get(url)

    content = response.content.decode("utf-8")
    assert '<script id="chart-finished-data" type="application/json">' in content


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
    response = client_logged.get(url, {"tab": "all"})
    actual = response.context["object_list"]
    assert len(actual) == 2


def test_list_all_books_lists_another_year(client_logged):
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 31), title="Old Book")

    url = reverse("books:list")
    actual = client_logged.get(url, {"tab": "all"}).content.decode("utf-8")

    assert "Old Book" in actual
    assert "1974-01-01" in actual


def test_list_empty_state_names_the_year(client_logged):
    url = reverse("books:list")
    actual = client_logged.get(url).content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra" in actual


def test_list_all_books_empty_state_does_not_name_a_year(client_logged):
    """?tab=all lists every year, so its empty state has no year to name."""
    url = reverse("books:list")
    actual = client_logged.get(url, {"tab": "all"}).content.decode("utf-8")

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
    assert f"Ar tikrai norite ištrinti: <strong>Book Title</strong>?" in actual


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

    index = client_logged.get(reverse("books:index")).content.decode("utf-8")
    assert f'hx-get="{reverse("books:list")}"' in index

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
