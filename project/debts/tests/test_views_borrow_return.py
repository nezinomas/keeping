from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from mock import patch

from ...accounts.factories import AccountFactory
from .. import factories, models, views

pytestmark = pytest.mark.django_db


def test_borrow_return_list_func():
    view = resolve('/debts/XXX/return/lists/')

    assert views.DebtReturnLists == view.func.view_class


def test_borrow_return_list_200(client_logged):
    url = reverse('debts:return_list', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_list_empty(client_logged):
    url = reverse('debts:return_list', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_borrow_return_list_with_data(client_logged):
    factories.BorrowReturnFactory()
    factories.LendReturnFactory(price=6.6)

    url = reverse('debts:return_list', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Suma' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Borrow Return Remark' in content

    assert '6,6' not in content


def test_borrow_return_list_edit_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:return_list', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:return_update', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})

    assert f'<a role="button" hx-get="{ link }"' in content


def test_borrow_return_list_delete_button(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:return_list', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('debts:return_delete', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})

    assert f'<a role="button" hx-get="{ link }"' in content


def test_borrow_return_new_func():
    view = resolve('/debts/XXX/return/new/')

    assert views.DebtReturnNew == view.func.view_class


def test_borrow_return_new_200(client_logged):
    url = reverse('debts:return_new', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_form(client_logged):
    url = reverse('debts:return_new', kwargs={'debt_type': 'borrow'})
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert f'hx-post="{url}"' in content


@patch('project.core.lib.utils.get_request_kwargs', return_value='borrow')
def test_borrow_return_save(mck, client_logged):
    a = AccountFactory()
    b = factories.BorrowFactory()

    data = {'date': '1999-1-3', 'debt': b.pk, 'price': '1.1', 'account': a.pk}
    url = reverse('debts:return_new', kwargs={'debt_type': 'borrow'})
    client_logged.post(url, data, follow=True)

    actual = models.DebtReturn.objects.items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == 'Account1'
    assert actual.price == Decimal('1.1')


def test_borrow_return_save_invalid_data(client_logged):
    data = {'borrow': 'A', 'price': '0'}
    url = reverse('debts:return_new', kwargs={'debt_type': 'borrow'})
    response = client_logged.post(url, data)
    form = response.context['form']

    assert not form.is_valid()


def test_borrow_return_update_func():
    view = resolve('/debts/XXX/return/update/1/')

    assert views.DebtReturnUpdate == view.func.view_class


def test_borrow_return_update_200(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:return_update', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_load_update_form(client_logged):
    obj = factories.BorrowReturnFactory()
    url = reverse('debts:return_update', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)
    form = response.context['form'].as_p()

    assert '5' in form
    assert 'Account1' in form
    assert 'Borrow Return Remark' in form


@patch('project.core.lib.utils.get_request_kwargs', return_value='borrow')
def test_borrow_return_update(mck, client_logged):
    debt = factories.BorrowFactory()
    e = factories.BorrowReturnFactory(debt=debt)
    a = AccountFactory(title='AAA')

    assert models.Debt.objects.items().get(pk=debt.pk).returned == Decimal('5')

    data = {
        'date': '1999-1-2',
        'price': '10',
        'remark': 'Pastaba',
        'account': a.pk,
        'debt': debt.pk
    }
    url = reverse('debts:return_update', kwargs={'pk': e.pk, 'debt_type': 'borrow'})
    client_logged.post(url, data)

    actual = models.DebtReturn.objects.get(pk=e.pk)
    assert actual.debt == debt
    assert actual.date == date(1999, 1, 2)
    assert actual.price == Decimal('10')
    assert actual.account.title == 'AAA'
    assert actual.remark == 'Pastaba'
    assert models.Debt.objects.items().get(pk=debt.pk).returned == Decimal('10')


@patch('project.core.lib.utils.get_request_kwargs', return_value='borrow')
def test_borrow_return_update_with_returns(mck, client_logged):
    debt = factories.BorrowFactory()
    factories.BorrowReturnFactory(debt=debt, price=40)
    factories.BorrowReturnFactory(debt=debt, price=50)
    e = factories.BorrowReturnFactory(debt=debt, price=5)
    a = AccountFactory(title='AAA')

    data = {
        'date': '1999-1-2',
        'price': '6',
        'remark': 'Pastaba',
        'account': a.pk,
        'debt': debt.pk
    }
    url = reverse('debts:return_update', kwargs={'pk': e.pk, 'debt_type': 'borrow'})
    response = client_logged.post(url, data, follow=True)

    assert not response.context.get('form')


def test_borrow_return_update_not_load_other_journal(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(journal=j1, title='a1')
    a2 = AccountFactory(journal=j2, title='a2')
    d1 = factories.BorrowFactory(account=a1, journal=j1)
    d2 = factories.BorrowFactory(account=a2, journal=j2)

    factories.BorrowReturnFactory(debt=d1, account=a1)
    obj = factories.BorrowReturnFactory(debt=d2, account=a2, price=666)

    url = reverse('debts:return_update', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_borrow_return_delete_func():
    view = resolve('/debts/XXX/return/delete/1/')

    assert views.DebtReturnDelete == view.func.view_class


def test_borrow_return_delete_200(client_logged):
    f = factories.BorrowReturnFactory()

    url = reverse('debts:return_delete', kwargs={'pk': f.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_borrow_return_delete_load_form(client_logged):
    obj = factories.BorrowReturnFactory()

    url = reverse('debts:return_delete', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.status_code == 200
    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_borrow_return_delete(client_logged):
    p = factories.BorrowReturnFactory()

    assert models.DebtReturn.objects.all().count() == 1

    url = reverse('debts:return_delete', kwargs={'pk': p.pk, 'debt_type': 'borrow'})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert models.DebtReturn.objects.all().count() == 0


def test_borrow_return_delete_other_journal_get_form(client_logged, second_user):
    d = factories.BorrowFactory(journal=second_user.journal)
    obj = factories.BorrowReturnFactory(debt=d)

    url = reverse('debts:return_delete', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_borrow_return_delete_other_journal_post_form(client_logged, second_user):
    d = factories.BorrowFactory(journal=second_user.journal)
    obj = factories.BorrowReturnFactory(debt=d)

    url = reverse('debts:return_delete', kwargs={'pk': obj.pk, 'debt_type': 'borrow'})
    client_logged.post(url, follow=True)

    assert models.DebtReturn.objects.all().count() == 1
