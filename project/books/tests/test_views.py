import json
from datetime import date

import pandas as pd  # must be load before freezegun, why?
import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ..factories import BookFactory
from ..views import Lists, New, Update

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


def test_view_lists_func():
    view = resolve('/books/')

    assert Lists == view.func.view_class


def test_view_new_func():
    view = resolve('/books/new/')

    assert New == view.func.view_class


def test_view_update_func():
    view = resolve('/books/update/1/')

    assert Update == view.func.view_class


@freeze_time('1999-01-01')
def test_load_book_form(admin_client):
    url = reverse('books:books_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="started" value="1999-01-01"' in actual['html_form']


@pytest.mark.django_db()
def test_save_book(client, login):
    data = {'started': '1999-01-01', 'author': 'AAA', 'title': 'TTT'}

    url = reverse('books:books_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert 'TTT' in actual['html_list']


@pytest.mark.django_db()
def test_books_save_invalid_data(client, login):
    data = {'started': 'x', 'author': 'A', 'title': 'T'}

    url = reverse('books:books_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_book_update(client, login):
    book = BookFactory()

    data = {
        'started': '1999-01-01',
        'ended': '1999-01-31',
        'author': 'AAA',
        'title': 'TTT'
    }
    url = reverse('books:books_update', kwargs={'pk': book.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '1999-01-01' in actual['html_list']
    assert '1999-01-31' in actual['html_list']
    assert 'AAA' in actual['html_list']
    assert 'TTT' in actual['html_list']
