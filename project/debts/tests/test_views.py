import json
import re

import pytest
from django.http.response import JsonResponse
from django.urls import resolve, reverse

from ...users.factories import UserFactory
from .. import views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                  Reload
# ---------------------------------------------------------------------------------------
def test_borrow_reload_func():
    view = resolve('/borrows/reload/')

    assert views.BorrowReload is view.func.view_class


def test_borrow_reload_render(rf):
    request = rf.get('/borrows/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.BorrowReload.as_view()(request)

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert 'borrow' in actual
    assert 'borrow_return' in actual


def test_borrow_reload_return_object(rf):
    request = rf.get('/borrows/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.BorrowReload.as_view()(request)

    assert isinstance(response, JsonResponse)


def test_borrow_reload_ender_trigger_not_set(client_logged):
    url = reverse('debts:borrows_reload')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_lent_reload_func():
    view = resolve('/lents/reload/')

    assert views.LentReload is view.func.view_class


def test_lent_reload_render(rf):
    request = rf.get('/lents/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.LentReload.as_view()(request)

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert 'lent' in actual
    assert 'lent_return' in actual


def test_lent_reload_return_object(rf):
    request = rf.get('/lents/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.LentReload.as_view()(request)

    assert isinstance(response, JsonResponse)


def test_lent_reload_ender_trigger_not_set(client_logged):
    url = reverse('debts:lents_reload')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                             Debts Index
# ---------------------------------------------------------------------------------------
def test_debts_index_func():
    view = resolve('/debts/')

    assert views.Index == view.func.view_class


def test_debts_index_200(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_debts_index_not_logged(client):
    url = reverse('debts:debts_index')
    response = client.get(url)

    assert response.status_code == 302


def test_debts_index_borrow_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'borrow' in response.context
    assert 'id="borrow"' in content


def test_debts_index_borrow_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'borrow_return' in response.context
    assert 'id="borrow_return"' in content


def test_debts_index_lent_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent' in response.context
    assert 'id="lent"' in content


def test_debts_index_lent_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent_return' in response.context
    assert 'id="lent_return"' in content


def test_debts_index_borrow_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:borrows_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_borrow_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:borrows_return_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


def test_debts_index_lent_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:lents_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_lent_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:lents_return_new')
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'