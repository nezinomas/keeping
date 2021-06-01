import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import factories, models, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

pytestmark = pytest.mark.django_db


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
    assert '<div id="borrow_ajax"' in content


def test_debts_index_borrow_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'borrow_return' in response.context
    assert '<div id="borrow_return_ajax"' in content


def test_debts_index_lent_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent' in response.context
    assert '<div id="lent_ajax"' in content


def test_debts_index_lent_return_in_ctx(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'lent_return' in response.context
    assert '<div id="lent_return_ajax"' in content


# ---------------------------------------------------------------------------------------
#                                                                                  Borrow
# ---------------------------------------------------------------------------------------
def test_borrow_list_func():
    view = resolve('/borrows/lists/')

    assert views.BorrowLists == view.func.view_class


def test_borrow_list_200(client_logged):
    url = reverse('debts:borrow_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_list_empty(client_logged):
    url = reverse('debts:borrow_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_list_with_data(client_logged):
    factories.BorrowFactory()

    url = reverse('debts:borrow_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolininkas' in content
    assert 'Paskolinta' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-01' in content
    assert 'Name' in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Borrow Remark' in content


# ---------------------------------------------------------------------------------------
#                                                                           Borrow Return
# ---------------------------------------------------------------------------------------
def test_borrow_return_list_func():
    view = resolve('/borrows/return/lists/')

    assert views.BorrowReturnLists == view.func.view_class


def test_borrow_return_list_200(client_logged):
    url = reverse('debts:borrow_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_list_empty(client_logged):
    url = reverse('debts:borrow_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_return_list_with_data(client_logged):
    factories.BorrowReturnFactory()

    url = reverse('debts:borrow_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Kiek' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Borrow Return Remark' in content


# ---------------------------------------------------------------------------------------
#                                                                                    Lent
# ---------------------------------------------------------------------------------------
def test_lent_list_func():
    view = resolve('/lents/lists/')

    assert views.LentLists == view.func.view_class


def test_lent_list_200(client_logged):
    url = reverse('debts:lent_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_list_empty(client_logged):
    url = reverse('debts:lent_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lent_list_with_data(client_logged):
    factories.LentFactory()

    url = reverse('debts:lent_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Skolintojas' in content
    assert 'Pasiskolinta' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-01' in content
    assert 'Name' in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Lent Remark' in content


# ---------------------------------------------------------------------------------------
#                                                                             Lent Return
# ---------------------------------------------------------------------------------------
def test_lent_return_list_func():
    view = resolve('/lents/return/lists/')

    assert views.LentReturnLists == view.func.view_class


def test_lent_return_list_200(client_logged):
    url = reverse('debts:lent_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_list_empty(client_logged):
    url = reverse('debts:lent_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lent_return_list_with_data(client_logged):
    factories.LentReturnFactory()

    url = reverse('debts:lent_return_list')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Kiek' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Lent Return Remark' in content
