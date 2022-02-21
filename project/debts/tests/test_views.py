import json
import re

import pytest
from django.http.response import JsonResponse
from django.urls import resolve, reverse
from mock import patch

from ...users.factories import UserFactory
from .. import factories, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                  Reload
# ---------------------------------------------------------------------------------------
def test_debt_reload_func():
    view = resolve('/debts/XXX/reload/')

    assert views.DebtReload is view.func.view_class


def test_debt_reload_lend_render(rf):
    request = rf.get('/debts/lend/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.DebtReload.as_view()(request, debt_type='lend')

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert 'lend' in actual
    assert 'lend_return' in actual


def test_debt_reload_borrow_render(rf):
    request = rf.get('/debts/borrow/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.DebtReload.as_view()(request, debt_type='borrow')

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert 'borrow' in actual
    assert 'borrow_return' in actual


def test_debt_reload_return_object(rf):
    request = rf.get('/debts/XXX/reload/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.DebtReload.as_view()(request)

    assert isinstance(response, JsonResponse)


def test_debt_reload_trigger_not_set(client_logged):
    url = reverse('debts:debts_reload', kwargs={'debt_type': 'XXX'})
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


def test_debts_index_lend_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lend' in response.context
    assert 'id="lend"' in content


def test_debts_index_lend_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lend_return' in response.context
    assert 'id="lend_return"' in content


def test_debts_index_borrow_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:debts_new', kwargs={'debt_type': 'borrow'})
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_borrow_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:debts_return_new', kwargs={'debt_type': 'borrow'})
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


def test_debts_index_lend_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:debts_new', kwargs={'debt_type': 'lend'})
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_lend_return_add_button(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:debts_return_new', kwargs={'debt_type': 'lend'})
    pattern = re.compile(fr'<button type="button".+data-url="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


def test_debts_index_with_data(client_logged):
    obj1 = factories.LendFactory(price=666)
    obj2 = factories.LendFactory(price=777)

    url = reverse('debts:debts_index')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert obj1.name in content
    assert '666,0' in content

    assert obj2.name in content
    assert '777,0' in content
