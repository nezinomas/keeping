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


def test_lent_return_list_func():
    view = resolve('/lents/return/lists/')

    assert views.LentReturnLists == view.func.view_class


def test_lent_return_list_200(client_logged):
    url = reverse('debts:lents_return_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_list_empty(client_logged):
    url = reverse('debts:lents_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert '<b>1999</b> metais įrašų nėra' in content


def test_lent_return_list_with_data(client_logged):
    factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    assert 'Data' in content
    assert 'Suma' in content
    assert 'Sąskaita' in content
    assert 'Pastaba' in content

    assert '1999-01-02' in content
    assert '5,0' in content
    assert 'Account1' in content
    assert 'Lent Return Remark' in content


def test_lent_return_list_edit_button(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_return_update', kwargs={'pk': f.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


def test_lent_return_list_delete_button(client_logged):
    obj = factories.LentReturnFactory()

    url = reverse('debts:lents_return_list')
    response = client_logged.get(url, {}, **X_Req)
    content = response.content.decode('utf-8')

    link = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})

    assert f'<a role="button" data-url="{ link }" data-target="lent"' in content
    assert 'js-create set-target' in content


def test_lent_return_new_func():
    view = resolve('/lents/return/new/')

    assert views.LentReturnNew == view.func.view_class


def test_lent_return_new_200(client_logged):
    url = reverse('debts:lents_return_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_load_form(client_logged):
    url = reverse('debts:lents_return_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200


def test_lent_return_save(client_logged):
    a = AccountFactory()
    b = factories.LentFactory()

    data = {'date': '1999-1-3', 'lent': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.LentReturn.objects.items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == 'Account1'
    assert actual.price == Decimal('1.1')


def test_lent_return_save_not_render_html_list(client_logged):
    a = AccountFactory()
    b = factories.LentFactory()

    data = {'date': '1999-1-3', 'lent': b.pk, 'price': '1.1', 'account': a.pk}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lent_return_save_invalid_data(client_logged):
    data = {'lent': 'A', 'price': '0'}

    url = reverse('debts:lents_return_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_lent_return_update_func():
    view = resolve('/lents/return/update/1/')

    assert views.LentReturnUpdate == view.func.view_class


def test_lent_return_update_200(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_update', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_load_update_form(client_logged):
    f = factories.LentReturnFactory()
    url = reverse('debts:lents_return_update', kwargs={'pk': f.pk})

    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert '5' in form
    assert 'Account1' in form
    assert 'Lent Return Remark' in form


def test_lent_return_update(client_logged):
    e = factories.LentReturnFactory()
    l = factories.LentFactory()
    a = AccountFactory(title='AAA')

    data = {
        'date': '1999-1-2',
        'price': '15',
        'remark': 'Pastaba',
        'account': a.pk,
        'lent': l.pk
    }
    url = reverse('debts:lents_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.LentReturn.objects.get(pk=e.pk)

    assert actual.lent == l
    assert actual.date == date(1999, 1, 2)
    assert actual.price == Decimal('15')
    assert actual.account.title == 'AAA'
    assert actual.remark == 'Pastaba'
    assert models.Lent.objects.get(pk=l.pk).returned == Decimal('35')


def test_lent_return_update_not_load_other_journal(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(journal=j1, title='a1')
    a2 = AccountFactory(journal=j2, title='a2')
    d1 = factories.LentFactory(account=a1, journal=j1)
    d2 = factories.LentFactory(account=a2, journal=j2)

    factories.LentReturnFactory(lent=d1, account=a1)
    obj = factories.LentReturnFactory(lent=d2, account=a2, price=666)

    url = reverse('debts:lents_return_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert d2.name not in form
    assert str(obj.price) not in form


def test_lent_return_update_not_render_html_list(client_logged):
    e = factories.LentReturnFactory()
    l = factories.LentFactory()
    a = AccountFactory(title='AAA')

    data = {
        'date': '1999-1-3',
        'price': '150',
        'remark': 'Pastaba',
        'account': a.pk,
        'lent': l.pk
    }
    url = reverse('debts:lents_return_update', kwargs={'pk': e.pk})

    response = client_logged.post(url, data, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lent_return_delete_func():
    view = resolve('/lents/return/delete/1/')

    assert views.LentReturnDelete == view.func.view_class


def test_lent_return_delete_200(client_logged):
    f = factories.LentReturnFactory()

    url = reverse('debts:lents_return_delete', kwargs={'pk': f.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_lent_return_delete_load_form(client_logged):
    obj = factories.LentReturnFactory()

    url = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="lent_return">' in actual
    assert f'Ar tikrai norite ištrinti: <strong>{ obj }</strong>?' in actual


def test_lent_return_delete(client_logged):
    p = factories.LentReturnFactory()

    assert models.LentReturn.objects.all().count() == 1
    url = reverse('debts:lents_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.LentReturn.objects.all().count() == 0


def test_lent_return_delete_not_render_html_list(client_logged):
    p = factories.LentReturnFactory()

    assert models.LentReturn.objects.all().count() == 1
    url = reverse('debts:lents_return_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)

    assert not actual.get('html_list')


def test_lent_return_delete_other_journal_get_form(client_logged, second_user):
    d = factories.LentFactory(journal=second_user.journal)
    obj = factories.LentReturnFactory(lent=d)

    url = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


def test_lent_return_delete_other_journal_post_form(client_logged, second_user):
    d = factories.LentFactory(journal=second_user.journal)
    obj = factories.LentReturnFactory(lent=d)

    url = reverse('debts:lents_return_delete', kwargs={'pk': obj.pk})
    client_logged.post(url, **X_Req)

    assert models.LentReturn.objects.all().count() == 1
