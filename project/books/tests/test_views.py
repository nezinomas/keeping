import re
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...users.factories import UserFactory
from .. import models, views
from ..factories import Book, BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                             Books Index View
# ----------------------------------------------------------------------------
def test_index_func():
    view = resolve('/books/')

    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse('books:index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_books_index_add_button(client_logged):
    url = reverse('books:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('books:new')
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Knygą'


def test_books_index_add_target_button(get_user, client_logged):
    get_user.year = 1111
    get_user.save()

    url = reverse('books:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('books:target_new')
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == '1111 metų tikslą'


def test_books_index_search_form(client_logged):
    url = reverse('books:index')
    response = client_logged.get(url).content.decode('utf-8')

    assert '<input type="search" name="search" id="id_search"' in response


def test_books_index_context(client_logged):
    url = reverse('books:index')
    response = client_logged.get(url)

    assert 'year' in response.context
    assert 'all' in response.context
    assert 'books' in response.context
    assert 'chart' in response.context
    assert 'info' in response.context


# ----------------------------------------------------------------------------
#                                                                     Info Row
# ----------------------------------------------------------------------------
def test_info_row_func():
    view = resolve('/books/info_row/')

    assert views.InfoRow == view.func.view_class


def test_info_row_200(client_logged):
    url = reverse('books:info_row')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-07-18')
def test_info_row_html(client_logged):
    BookFactory()
    BookFactory()
    BookFactory(ended=date(1999, 2, 1))

    url = reverse('books:info_row')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    readed = re.compile(r'Perskaitytos:.*?(\d+)<\/h6>')
    assert re.findall(readed, content) == ['1']

    reading = re.compile(r'Skaitomos:.*?(\d+)<\/h6>')
    assert re.findall(reading, content) == ['2']


@freeze_time('1999-07-18')
def test_info_row_no_data(client_logged):
    url = reverse('books:info_row')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    readed = re.compile(r'Perskaitytos:.*?(\d+)<\/h6>')
    assert re.findall(readed, content) == ['0']

    reading = re.compile(r'Skaitomos:.*?(\d+)<\/h6>')
    assert re.findall(reading, content) == ['0']


def test_info_row_update_link(client_logged):
    t = BookTargetFactory()

    url = reverse('books:info_row')
    response = client_logged.get(url)

    content = response.content.decode('utf-8')
    link = reverse('books:target_update', kwargs={'pk': t.pk})

    pattern = re.compile(fr'<a role="button" hx-get="{ link }".*?>(\d+)<\/a>')
    res = re.findall(pattern, content)

    assert res[0] == '100'


def test_info_row_no_target(client_logged):
    url = reverse('books:info_row')
    response = client_logged.get(url)

    assert not 'Tikslas' in response.context


# ----------------------------------------------------------------------------
#                                                                 Readed Books
# ----------------------------------------------------------------------------
def test_chart_readed_func():
    view = resolve('/books/chart_readed/')

    assert views.ChartReaded == view.func.view_class


def test_chart_readed_200(client_logged):
    url = reverse('books:chart_readed')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_books_index_chart_year(client_logged):
    BookFactory(ended=date(1999, 1, 1))

    url = reverse('books:chart_readed')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_readed_books_container"></div>' in content


# ----------------------------------------------------------------------------
#                                                             Books Lists View
# ----------------------------------------------------------------------------
def test_lists_func():
    view = resolve('/books/lists/')

    assert views.Lists == view.func.view_class


def test_list_200(client_logged):
    url = reverse('books:list')
    response = client_logged.get(url)

    assert response.status_code == 200


# ----------------------------------------------------------------------------
#                                                        Books New/Update View
# ----------------------------------------------------------------------------
def test_view_new_func():
    view = resolve('/books/new/')

    assert views.New == view.func.view_class


def test_view_update_func():
    view = resolve('/books/update/1/')

    assert views.Update == view.func.view_class


@freeze_time('2000-01-01')
def test_load_books_form(client_logged):
    url = reverse('books:new')

    response = client_logged.get(url, {})

    actual = response.context['form'].as_p()

    assert response.status_code == 200
    assert '<input type="text" name="started" value="1999-01-01"' in actual


def test_save_book(client_logged):
    data = {'started': '1999-01-01', 'author': 'AAA', 'title': 'TTT'}

    url = reverse('books:new')

    response = client_logged.post(url, data, follow=True)

    assert response.resolver_match.func.view_class is views.Lists

    obj = Book.objects.first()

    assert obj.started == date(1999, 1, 1)
    assert obj.author == 'AAA'
    assert obj.title == 'TTT'


def test_books_save_invalid_data(client_logged):
    data = {'started': 'x', 'author': 'A', 'title': 'T'}

    url = reverse('books:new')

    response = client_logged.post(url, data)

    actual = response.context['form']

    assert not actual.is_valid()


def test_books_update(client_logged):
    book = BookFactory()

    data = {
        'started': '1999-01-01',
        'ended': '1999-01-31',
        'author': 'AAA',
        'title': 'TTT'
    }
    url = reverse('books:update', kwargs={'pk': book.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual
    assert '1999-01-31' in actual
    assert 'AAA' in actual
    assert 'TTT' in actual


def test_books_load_update_form(client_logged):
    i = BookFactory()
    url = reverse('books:update', kwargs={'pk': i.pk})

    response = client_logged.get(url, follow=True)
    form = response.context['form'].as_p()

    assert '1999-01-01' in form
    assert 'Author' in form
    assert 'Book Title' in form
    assert 'Remark' in form


def test_book_update_to_another_year(client_logged):
    income = BookFactory()

    data = {
        'started': '1999-12-31',
        'ended': '2010-12-31',
        'author': 'Author',
        'title': 'Book Title',
        'remark': 'Pastaba',
    }
    url = reverse('books:update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert '2010-12-31' not in actual


@freeze_time('2000-03-03')
def test_books_update_past_record(get_user, client_logged):
    get_user.year = 2000
    i = BookFactory(started=date(1974, 12, 12))

    data = {
        'started': '1999-03-03',
        'author': 'XXX',
        'title': 'YYY',
        'remark': 'ZZZ',
    }
    url = reverse('books:update', kwargs={'pk': i.pk})

    client_logged.post(url, data)

    actual = models.Book.objects.get(pk=i.pk)
    assert actual.started == date(1999, 3, 3)
    assert actual.author == 'XXX'
    assert actual.title == 'YYY'
    assert actual.remark == 'ZZZ'


def test_books_update_not_load_other_user(client_logged, second_user):
    BookFactory()
    obj = BookFactory(author='xxx', title='yyy', user=second_user)

    url = reverse('books:update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
#                                                                             Book Delete
# ---------------------------------------------------------------------------------------
def test_view_books_delete_func():
    view = resolve('/books/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_books_delete_200(client_logged):
    p = BookFactory()

    url = reverse('books:delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_books_delete_load_form(client_logged):
    p = BookFactory()

    url = reverse('books:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, follow=True)

    actual = response.content.decode('utf-8')

    assert '<form method="POST"' in actual
    assert f'Ar tikrai norite ištrinti: <strong>Book Title</strong>?' in actual


def test_view_books_delete(client_logged):
    p = BookFactory()

    assert models.Book.objects.all().count() == 1
    url = reverse('books:delete', kwargs={'pk': p.pk})

    client_logged.post(url, {}, follow=True)

    assert models.Book.objects.all().count() == 0


def test_books_delete_other_user_get_form(client_logged, second_user):
    obj = BookFactory(user=second_user)

    url = reverse('books:delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_books_delete_other_user_post_form(client_logged, second_user):
    obj = BookFactory(user=second_user)

    url = reverse('books:delete', kwargs={'pk': obj.pk})
    client_logged.post(url)

    assert models.Book.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                          Books Search
# ---------------------------------------------------------------------------------------
def test_search_func():
    view = resolve('/books/search/')

    assert views.Search is view.func.view_class


def test_search_get_200(client_logged):
    url = reverse('books:search')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_not_found(client_logged):
    BookFactory()

    url = reverse('books:search')
    response = client_logged.get(url, {'search': 'xxx'})
    actual = response.content.decode('utf-8')

    assert 'Nieko nerasta' in actual


def test_search_found(client_logged):
    BookFactory()

    url = reverse('books:search')
    response = client_logged.get(url, {'search': '1999 title'})
    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual
    assert 'Book Title' in actual
    assert 'Author' in actual


def test_search_pagination_first_page(client_logged):
    u = UserFactory()
    i = BookFactory.build_batch(51, user=u)
    Book.objects.bulk_create(i)

    url = reverse('books:search')
    response = client_logged.get(url, {'search': 'title'})
    actual = response.content.decode('utf-8')

    assert actual.count('Author') == 50


def test_search_pagination_second_page(client_logged):
    u = UserFactory()
    i = BookFactory.build_batch(51, user=u)
    Book.objects.bulk_create(i)

    url = reverse('books:search')

    response = client_logged.get(url, {'page': 2, 'search': 'author'})
    actual = response.content.decode('utf-8')

    assert actual.count('Author') == 1


# ---------------------------------------------------------------------------------------
#                                                                    Target Create/Update
# ---------------------------------------------------------------------------------------
def test_target(client_logged):
    url = reverse('books:target_new')

    response = client_logged.get(url, {})
    actual = response.content.decode('utf-8')

    assert '<input type="text" name="year" value="1999"' in actual


def test_target_new(client_logged):
    data = {'year': 1999, 'quantity': 66}
    url = reverse('books:target_new')
    client_logged.post(url, data)

    assert models.BookTarget.objects.first().quantity == 66


def test_target_new_invalid_data(client_logged):
    data = {'year': -2, 'quantity': 'x'}

    url = reverse('books:target_new')

    response = client_logged.post(url, data)

    form = response.context['form']

    assert not form.is_valid()


def test_target_update(client_logged):
    p = BookTargetFactory()

    data = {'year': 1999, 'quantity': 66}
    url = reverse('books:target_update', kwargs={'pk': p.pk})

    client_logged.post(url, data)

    assert models.BookTarget.objects.first().quantity == 66
