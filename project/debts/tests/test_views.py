import re

import pytest
from django.urls import resolve, reverse

from .. import factories, views

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                             Debts Index
# ---------------------------------------------------------------------------------------
def test_debts_index_func():
    view = resolve('/debts/')

    assert views.Index == view.func.view_class


def test_debts_index_200(client_logged):
    url = reverse('debts:index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_debts_index_not_logged(client):
    url = reverse('debts:index')
    response = client.get(url)

    assert response.status_code == 302


def test_debts_index_borrow_add_button(client_logged):
    url = reverse('debts:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:new', kwargs={'debt_type': 'borrow'})
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_borrow_return_add_button(client_logged):
    url = reverse('debts:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:return_new', kwargs={'debt_type': 'borrow'})
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'


def test_debts_index_lend_add_button(client_logged):
    url = reverse('debts:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:new', kwargs={'debt_type': 'lend'})
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Skolą'


def test_debts_index_lend_return_add_button(client_logged):
    url = reverse('debts:index')
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse('debts:return_new', kwargs={'debt_type': 'lend'})
    pattern = re.compile(fr'<button type="button".+hx-get="{ link }".+<\/i>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == 'Sumą'
