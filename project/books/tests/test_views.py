import json
import re
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...users.factories import UserFactory
from ..factories import BookFactory
from ..views import Index, Lists, New, ReloadStats, Update

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                             Books Index View
# ----------------------------------------------------------------------------
def test_view_index_func():
    view = resolve('/books/')

    assert Index == view.func.view_class


def test_books_index_200(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_books_index_context(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url)

    assert 'book_list' in response.context
    assert 'chart_readed_books' in response.context


def test_books_index_chart_year(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_readed_books"><div id="chart_readed_books_container"></div>' in content


@freeze_time('1999-07-18')
def test_books_index_info_row(client_logged):
    BookFactory()
    BookFactory()
    BookFactory(ended=date(1999, 2, 1))

    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    readed = re.compile(r'Perskaitytos:.*?(\d+)<\/h6>')
    assert re.findall(readed, content) == ['1']

    reading = re.compile(r'Skaitomos:.*?(\d+)<\/h6>')
    assert re.findall(reading, content) == ['2']


@freeze_time('1999-07-18')
def test_books_index_info_row_no_data(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    readed = re.compile(r'Perskaitytos:.*?(\d+)<\/h6>')
    assert re.findall(readed, content) == ['0']

    reading = re.compile(r'Skaitomos:.*?(\d+)<\/h6>')
    assert re.findall(reading, content) == ['0']


def test_books_index_add_button(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<button type="button".+data-url="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('books:books_new')
    assert res[0][1] == 'Knygą'


# ---------------------------------------------------------------------------------------
#                                                                            Realod Stats
# ---------------------------------------------------------------------------------------
def test_books_reload_stats_func():
    view = resolve('/books/reload_stats/')

    assert ReloadStats is view.func.view_class


def test_books_reload_stats_render(get_user, rf):
    request = rf.get('/books/reload_stats/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = ReloadStats.as_view()(request)

    assert response.status_code == 200


def test_books_reload_stats_render_ajax_trigger(client_logged):
    url = reverse('books:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200


def test_books_reload_stats_render_ajax_trigger_not_set(client_logged):
    url = reverse('books:reload_stats')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert Index == response.resolver_match.func.view_class


# ----------------------------------------------------------------------------
#                                                             Books Lists View
# ----------------------------------------------------------------------------
def test_view_lists_func():
    view = resolve('/books/lists/')

    assert Lists == view.func.view_class


# ----------------------------------------------------------------------------
#                                                        Books New/Update View
# ----------------------------------------------------------------------------
def test_view_new_func():
    view = resolve('/books/new/')

    assert New == view.func.view_class


def test_view_update_func():
    view = resolve('/books/update/1/')

    assert Update == view.func.view_class


@freeze_time('2000-01-01')
def test_load_books_form(client_logged):
    url = reverse('books:books_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="started" value="1999-01-01"' in actual['html_form']


def test_save_book(client_logged):
    data = {'started': '1999-01-01', 'author': 'AAA', 'title': 'TTT'}

    url = reverse('books:books_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert 'TTT' in actual['html_list']


def test_books_save_invalid_data(client_logged):
    data = {'started': 'x', 'author': 'A', 'title': 'T'}

    url = reverse('books:books_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_books_update(client_logged):
    book = BookFactory()

    data = {
        'started': '1999-01-01',
        'ended': '1999-01-31',
        'author': 'AAA',
        'title': 'TTT'
    }
    url = reverse('books:books_update', kwargs={'pk': book.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1999-01-31' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert 'TTT' in actual['html_list']
