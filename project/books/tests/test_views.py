import json
import re
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...users.factories import UserFactory
from .. import models
from ..factories import BookFactory, BookTargetFactory
from ..views import Delete, Index, Lists, New, ReloadStats, Search, Update

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


def test_books_index_add_target_button(get_user, client_logged):
    get_user.year = 1111
    get_user.save()

    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('books:books_target_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == ' 1111 metų tikslą'


def test_books_index_target_update_link(client_logged):
    t = BookTargetFactory()

    url = reverse('books:books_index')
    response = client_logged.get(url)

    content = response.content.decode()
    link = reverse('books:books_target_update', kwargs={'pk': t.pk})

    pattern = re.compile(fr'<a type="button" data-url="{ link }".*?>(\d+)<\/a>')
    res = re.findall(pattern, content)

    assert res[0] == '100'


def test_books_index_search_form(client_logged):
    url = reverse('books:books_index')
    response = client_logged.get(url).content.decode('utf-8')

    assert '<input type="text" name="search"' in response
    assert reverse('books:books_search') in response


# ---------------------------------------------------------------------------------------
#                                                                            Realod Stats
# ---------------------------------------------------------------------------------------
def test_books_reload_stats_func():
    view = resolve('/books/reload_stats/')

    assert ReloadStats is view.func.view_class


def test_books_reload_stats_render(rf):
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


def test_books_load_update_form(client_logged):
    i = BookFactory()
    url = reverse('books:books_update', kwargs={'pk': i.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

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
    url = reverse('books:books_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '2010-12-31' not in actual['html_list']


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
    url = reverse('books:books_update', kwargs={'pk': i.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Book.objects.get(pk=i.pk)
    assert actual.started == date(1999, 3, 3)
    assert actual.author == 'XXX'
    assert actual.title == 'YYY'
    assert actual.remark == 'ZZZ'


# ---------------------------------------------------------------------------------------
#                                                                             Book Delete
# ---------------------------------------------------------------------------------------
def test_view_books_delete_func():
    view = resolve('/books/delete/1/')

    assert Delete is view.func.view_class


def test_view_books_delete_200(client_logged):
    p = BookFactory()

    url = reverse('books:books_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_books_delete_load_form(client_logged):
    p = BookFactory()

    url = reverse('books:books_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/books/delete/1/"' in actual['html_form']


def test_view_books_delete(client_logged):
    p = BookFactory()

    assert models.Book.objects.all().count() == 1
    url = reverse('books:books_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Book.objects.all().count() == 0



# ---------------------------------------------------------------------------------------
#                                                                          Books Search
# ---------------------------------------------------------------------------------------
@pytest.fixture()
def _search_form_data():
    return ([
        {"name": "csrfmiddlewaretoken", "value": "xxx"},
        {"name": "search", "value": "1999 title"},
    ])


def test_search_func():
    view = resolve('/books/search/')

    assert Search is view.func.view_class


def test_search_get_200(client_logged):
    url = reverse('books:books_search')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_get_302(client):
    url = reverse('books:books_search')
    response = client.get(url)

    assert response.status_code == 302


def test_search_post_200(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)
    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 200


def test_search_post_404(client_logged):
    url = reverse('books:books_search')
    response = client_logged.post(url)

    assert response.status_code == 404


def test_search_post_500(client_logged):
    form_data = json.dumps([{'x': 'y'}])
    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_bad_json_data(client_logged):
    form_data = "{'x': 'y'}"
    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})

    assert response.status_code == 500


def test_search_form_is_not_valid(client_logged, _search_form_data):
    _search_form_data[1]['value'] = '@#$%^&*xxxx'  # search
    form_data = json.dumps(_search_form_data)

    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert not actual['form_is_valid']


def test_search_form_is_valid(client_logged, _search_form_data):
    form_data = json.dumps(_search_form_data)

    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert actual['form_is_valid']


def test_search_not_found(client_logged, _search_form_data):
    BookFactory()

    _search_form_data[1]['value'] = 'xxxx'
    form_data = json.dumps(_search_form_data)

    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert 'Nieko neradau' in actual['html']


def test_search_found(client_logged, _search_form_data):
    BookFactory()

    form_data = json.dumps(_search_form_data)

    url = reverse('books:books_search')
    response = client_logged.post(url, {'form_data': form_data})
    actual = json.loads(response.content)

    assert '1999-01-01' in actual['html']
    assert 'Book Title' in actual['html']
    assert 'Author' in actual['html']



# ---------------------------------------------------------------------------------------
#                                                                    Target Create/Update
# ---------------------------------------------------------------------------------------
def test_target(client_logged):
    url = reverse('books:books_target_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_target_new(client_logged):
    data = {'year': 1999, 'quantity': 66}

    url = reverse('books:books_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert models.BookTarget.objects.year(1999)[0].quantity == 66


def test_target_new_invalid_data(client_logged):
    data = {'year': -2, 'quantity': 'x'}

    url = reverse('books:books_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_target_update(client_logged):
    p = BookTargetFactory()

    data = {'year': 1999, 'quantity': 66}
    url = reverse('books:books_target_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert models.BookTarget.objects.year(1999)[0].quantity == 66


def test_target_empty_db(client_logged):
    response = client_logged.get('/books/')

    assert not 'Tikslas' in response.context["info_row"]
