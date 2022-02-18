import json
from datetime import date
from decimal import Decimal

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from ...accounts.factories import AccountFactory
from .. import factories, models, views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


def test_lend_list_func():
    view = resolve('/debts/XXX/lists/')

    assert views.DebtLists == view.func.view_class


def test_lend_list_200(client_logged):
    url = reverse('debts:debts_list', kwargs={'type': 'lend'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lend_list_empty(client_logged):
    factories.BorrowFactory(price=666)

    url = reverse('debts:debts_list', kwargs={'type': 'lend'})
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lend_list_with_data(client_logged):
    obj1 = factories.LendFactory(closed=True)
    obj2 = factories.BorrowFactory(price=666)

    url = reverse('debts:debts_list', kwargs={'type': 'lend'})
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Paskolos gavėjas' in content
    assert 'Suma' in content
    assert 'Gražinta' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content
    assert 'Uždaryta' in content

    assert '1999-01-01' in content
    assert obj1.name in content
    assert '100,0' in content
    assert '25,0' in content
    assert 'Account1' in content
    assert 'Lend Remark' in content
    assert '<i class="bi bi-check-circle-fill"></i>' in content

    assert obj2.name not in content
    assert '666,0' not in content


def test_lend_list_edit_button(client_logged):
    obj = factories.LendFactory()

    url = reverse('debts:debts_list', kwargs={'type': 'lend'})
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:debts_update', kwargs={'pk': obj.pk, 'type': 'lend'})

    assert f'<a role="button" data-url="{ link }" data-target="lend"' in content
    assert 'js-create set-target' in content


def test_lend_list_delete_button(client_logged):
    obj = factories.LendFactory()

    url = reverse('debts:debts_list', kwargs={'type': 'lend'})
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:debts_delete', kwargs={'pk': obj.pk, 'type': 'lend'})

    assert f'<a role="button" data-url="{ link }" data-target="lend"' in content
    assert 'js-create set-target' in content


def test_lend_new_func():
    view = resolve('/debts/XXX/new/')

    assert views.DebtNew == view.func.view_class


def test_lend_new_200(client_logged):
    url = reverse('debts:debts_new', kwargs={'type': 'lend'})
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('2000-01-01')
def test_lend_load_form(client_logged):
    url = reverse('debts:debts_new', kwargs={'type': 'lend'})

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_save(mck, client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:debts_new', kwargs={'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert not actual.get('html_list')

    actual = models.Debt.objects.items()[0]
    assert actual.date == date(1999, 1, 1)
    assert actual.account.title == 'Account1'
    assert actual.name == 'AAA'
    assert actual.price == Decimal('1.1')
    assert actual.type == 'lend'


def test_lend_save_not_render_html_list(client_logged):
    a = AccountFactory()
    data = {'date': '1999-01-01', 'name': 'AAA', 'price': '1.1', 'account': a.pk}

    url = reverse('debts:debts_new', kwargs={'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lend_save_invalid_data(client_logged):
    data = {'date': 'x', 'name': 'A', 'price': '0'}

    url = reverse('debts:debts_new', kwargs={'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_lend_update_func():
    view = resolve('/debts/lend/update/1/')

    assert views.DebtUpdate == view.func.view_class


def test_lend_update_200(client_logged):
    f = factories.LendFactory()

    url = reverse('debts:debts_update', kwargs={'pk': f.pk, 'type': 'lend'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lend_load_update_form(client_logged):
    f = factories.LendFactory()
    url = reverse('debts:debts_update', kwargs={'pk': f.pk, 'type': 'lend'})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '1999-01-01' in form
    assert '100' in form
    assert 'Account1' in form
    assert 'Lend Remark' in form


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_update(mck, client_logged):
    e = factories.LendFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': False
    }
    url = reverse('debts:debts_update', kwargs={'pk': e.pk, 'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Debt.objects.items()
    assert actual.count() == 1

    actual = actual[0]
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert not actual.closed


def test_lend_update_not_closed(client_logged):
    e = factories.LendFactory(name='XXX')

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': False
    }
    url = reverse('debts:debts_update', kwargs={'pk': e.pk, 'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.Debt.objects.get(pk=e.pk)
    assert actual.name == 'XXX'
    assert actual.date == date(1999, 12, 31)
    assert actual.price == Decimal('150')
    assert actual.account.title == 'Account1'
    assert actual.remark == 'Pastaba'
    assert not actual.closed


def test_lend_update_price_smaller_then_returned(client_logged):
    e = factories.LendFactory(name='XXX')

    data = {
        'name': 'XXX',
        'price': '5',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': False
    }
    url = reverse('debts:debts_update', kwargs={'pk': e.pk, 'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']
    assert 'Negalite atnaujinti į mažesnę sumą nei jau sugrąžinta suma.' in  actual['html_form']


def test_lend_update_cant_close(client_logged):
    e = factories.LendFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }
    url = reverse('debts:debts_update', kwargs={'pk': e.pk, 'type': 'lend'})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']
    assert 'Negalite uždaryti dar negražintos skolos.' in actual['html_form']


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_update_not_render_html_list(mck, client_logged):
    e = factories.LendFactory()

    data = {
        'name': 'XXX',
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'closed': True
    }

    url = reverse('debts:debts_update', kwargs={'pk': e.pk, 'type': 'lend'})
    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lend_update_not_load_other_journal(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(journal=j1, title='a1')
    a2 = AccountFactory(journal=j2, title='a2')

    factories.LendFactory(name='xxx', journal=j1, account=a1)
    obj = factories.LendFactory(name='yyy', price=666, journal=j2, account=a2)

    url = reverse('debts:debts_update', kwargs={'pk': obj.pk, 'type': 'lend'})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert obj.name not in form
    assert str(obj.price) not in form


def test_lend_delete_func():
    view = resolve('/debts/XXX/delete/1/')

    assert views.DebtDelete == view.func.view_class


def test_lend_delete_200(client_logged):
    f = factories.LendFactory()

    url = reverse('debts:debts_delete', kwargs={'pk': f.pk, 'type': 'lend'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lend_delete_load_form(client_logged):
    obj = factories.LendFactory()

    url = reverse('debts:debts_delete', kwargs={'pk': obj.pk, 'type': 'lend'})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="lend">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_lend_delete(client_logged):
    p = factories.LendFactory()

    assert models.Debt.objects.all().count() == 1
    url = reverse('debts:debts_delete', kwargs={'pk': p.pk, 'type': 'lend'})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Debt.objects.all().count() == 0


def test_lend_delete_not_render_html_list(client_logged):
    p = factories.LendFactory()

    assert models.Debt.objects.all().count() == 1
    url = reverse('debts:debts_delete', kwargs={'pk': p.pk, 'type': 'lend'})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lend_delete_other_journal_get_form(client_logged, second_user):
    obj = factories.LendFactory(name='yyy', journal=second_user.journal)

    url = reverse('debts:debts_delete', kwargs={'pk': obj.pk, 'type': 'lend'})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


def test_lend_delete_other_journal_post_form(client_logged, second_user):
    obj = factories.LendFactory(name='yyy', journal=second_user.journal)

    url = reverse('debts:debts_delete', kwargs={'pk': obj.pk, 'type': 'lend'})
    client_logged.post(url, **X_Req)

    assert models.Debt.objects.all().count() == 1
