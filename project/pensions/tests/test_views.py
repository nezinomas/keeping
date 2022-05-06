import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from .. import models, views
from ..factories import Pension, PensionFactory, PensionTypeFactory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                Pensions
# ---------------------------------------------------------------------------------------
def test_pensions_lists_func():
    view = resolve('/pensions/lists/')

    assert views.Lists == view.func.view_class


def test_pensions_new_func():
    view = resolve('/pensions/new/')

    assert views.New == view.func.view_class


def test_pensions_update_func():
    view = resolve('/pensions/update/1/')

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve('/pensions/type/')

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve('/pensions/type/new/')

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve('/pensions/type/update/1/')

    assert views.TypeUpdate == view.func.view_class


@freeze_time('2000-01-01')
def test_pensions_load_form(admin_client):
    url = reverse('pensions:new')

    response = admin_client.get(url)
    form = response.context['form']

    assert '2000-01-01' in form.as_p()


def test_pensions_save(client_logged):
    i = PensionTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'pension_type': i.pk
    }

    url = reverse('pensions:new')

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual
    assert '1,05' in actual
    assert 'PensionType' in actual


def test_pensions_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'pension_type': 'x'
    }

    url = reverse('pensions:new')

    response = client_logged.post(url, data)

    form = response.context['form']

    assert not form.is_valid()


def test_pensions_update_to_another_year(client_logged):
    income = PensionFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'pension_type': 1,
    }
    url = reverse('pensions:update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = response.content.decode('utf-8')

    assert '2010-12-31' not in actual


def test_pensions_update(client_logged):
    income = PensionFactory()

    data = {
        'price': '150',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'pension_type': 1
    }
    url = reverse('pensions:update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = response.content.decode('utf-8')

    assert '1999-12-31' in actual
    assert '150' in actual
    assert 'Pastaba' in actual


def test_pensions_not_load_other_journal(client_logged, main_user, second_user):
    it1 = PensionTypeFactory(title='xxx', journal=main_user.journal)
    it2 = PensionTypeFactory(title='yyy', journal=second_user.journal)

    PensionFactory(pension_type=it1)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse('pensions:update', kwargs={'pk': i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
#                                                                           Pension Delete
# ---------------------------------------------------------------------------------------
def test_view_pensions_delete_func():
    view = resolve('/pensions/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_pensions_delete_200(client_logged):
    p = PensionFactory()

    url = reverse('pensions:delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_pensions_delete_load_form(client_logged):
    p = PensionFactory()

    url = reverse('pensions:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)
    form = response.content.decode('utf-8')

    assert '<form method="POST"' in form
    assert f'Ar tikrai norite ištrinti: <strong>{p}</strong>?' in form


def test_view_pensions_delete(client_logged):
    p = PensionFactory()

    assert models.Pension.objects.all().count() == 1
    url = reverse('pensions:delete', kwargs={'pk': p.pk})

    client_logged.post(url, follow=True)

    assert models.Pension.objects.all().count() == 0


def test_pensions_delete_other_journal_get_form(client_logged, second_user):
    it2 = PensionTypeFactory(title='yyy', journal=second_user.journal)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse('pensions:delete', kwargs={'pk': i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_pensions_delete_other_journal_post_form(client_logged, second_user):
    it2 = PensionTypeFactory(title='yyy', journal=second_user.journal)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse('pensions:delete', kwargs={'pk': i2.pk})
    client_logged.post(url)

    assert Pension.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                             PensionType
# ---------------------------------------------------------------------------------------

@freeze_time('2000-01-01')
def test_type_load_form(admin_client):
    url = reverse('pensions:type_new')

    response = admin_client.get(url)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_type_save(client_logged):
    data = {'title': 'TTT'}
    url = reverse('pensions:type_new')

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('pensions:type_new')

    response = client_logged.post(url, data, follow=True)

    form = response.context['form']

    assert not form.is_valid()


def test_type_update(client_logged):
    income = PensionTypeFactory()

    data = {'title': 'TTT'}
    url = reverse('pensions:type_update', kwargs={'pk': income.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_pension_type_not_load_other_journal(client_logged, main_user, second_user):
    PensionTypeFactory(title='xxx', journal=main_user.journal)
    obj = PensionTypeFactory(title='yyy', journal=second_user.journal)

    url = reverse('pensions:type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404
