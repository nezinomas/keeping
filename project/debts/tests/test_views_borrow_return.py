import json
from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import factories, models, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


def test_borrow_return_list_func():
    view = resolve('/borrows/return/lists/')

    assert views.BorrowReturnLists == view.func.view_class


def test_borrow_return_list_200(client_logged):
    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_list_empty(client_logged):
    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_return_list_with_data(client_logged):
    factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Suma' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Borrow Return Remark' in content


def test_borrow_return_list_edit_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content


def test_borrow_return_list_delete_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:borrows_return_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="borrow"' in content
    assert 'js-create set-target' in content


def test_borrow_return_new_func():
    view = resolve('/borrows/return/new/')

    assert views.BorrowReturnNew == view.func.view_class


def test_borrow_return_new_200(client_logged):
    url = reverse('debts:borrows_return_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_form(client_logged):
    url = reverse('debts:borrows_return_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200


def test_borrow_return_save(client_logged):
    a = AccountFactory()
    b = factories.BorrowFactory()

    data = {'date': '1999-1-3', 'borrow': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.BorrowReturn.objects.items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == 'Account1'
    assert actual.price == Decimal('1.1')


def test_borrow_return_save_not_render_html_list(client_logged):
    a = AccountFactory()
    b = factories.BorrowFactory()

    data = {'date': '1999-1-3', 'borrow': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_borrow_return_save_invalid_data(client_logged):
    data = {'borrow': 'A', 'price': '0'}

    url = reverse('debts:borrows_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_borrow_return_update_func():
    view = resolve('/borrows/return/update/1/')

    assert views.BorrowReturnUpdate == view.func.view_class


def test_borrow_return_update_200(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_update_form(client_logged):
    obj = factories.BorrowReturnFactory()
    url = reverse('debts:borrows_return_update', kwargs={'pk': obj.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '5' in form
    assert 'Account1' in form
    assert 'Borrow Return Remark' in form


def test_borrow_return_update(client_logged):
    e = factories.BorrowReturnFactory()
    l = factories.BorrowFactory()
    a = AccountFactory(title='AAA')

    data = {
        'date': '1999-1-2',
        'price': '10',
        'remark': 'Pastaba',
        'account': a.pk,
        'borrow': l.pk
    }
    url = reverse('debts:borrows_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.BorrowReturn.objects.get(pk=e.pk)

    assert actual.borrow == l
    assert actual.date == date(1999, 1, 2)
    assert actual.price == Decimal('10')
    assert actual.account.title == 'AAA'
    assert actual.remark == 'Pastaba'
    assert models.Borrow.objects.items().get(pk=l.pk).returned == Decimal('30')


def test_borrow_return_update_not_render_html_list(client_logged):
    e = factories.BorrowReturnFactory()
    l = factories.BorrowFactory()
    a = AccountFactory(title='AAA')

    data = {
        'date': '1999-1-3',
        'price': '150',
        'remark': 'Pastaba',
        'account': a.pk,
        'borrow': l.pk
    }
    url = reverse('debts:borrows_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_borrow_return_delete_func():
    view = resolve('/borrows/return/delete/1/')

    assert views.BorrowReturnDelete == view.func.view_class


def test_borrow_return_delete_200(client_logged):
    f = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_delete_load_form(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:borrows_return_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="borrow_return">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_borrow_return_delete(client_logged):
    p = factories.BorrowReturnFactory()

    assert models.BorrowReturn.objects.all().count() == 1
    url = reverse('debts:borrows_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.BorrowReturn.objects.all().count() == 0


def test_borrow_return_delete_not_render_html_list(client_logged):
    p = factories.BorrowReturnFactory()

    assert models.BorrowReturn.objects.all().count() == 1
    url = reverse('debts:borrows_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')
