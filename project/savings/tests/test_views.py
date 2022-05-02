import json
from urllib import response

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...core.tests.utils import setup_view
from .. import models, views
from ..factories import Saving, SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


def test_index_func():
    view = resolve('/savings/')

    assert views.Index == view.func.view_class


def test_savings_lists_func():
    view = resolve('/savings/lists/')

    assert views.Lists == view.func.view_class


def test_savings_new_func():
    view = resolve('/savings/new/')

    assert views.New == view.func.view_class


def test_savings_update_func():
    view = resolve('/savings/update/1/')

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve('/savings/type/')

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve('/savings/type/new/')

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve('/savings/type/update/1/')

    assert views.TypeUpdate == view.func.view_class


def test_index_view_context(client_logged):
    url = reverse('savings:index')
    response = client_logged.get(url)
    context = response.context

    assert 'saving' in context
    assert 'saving_type' in context
    assert 'pension' in context
    assert 'pension_type' in context


@freeze_time('2000-01-01')
def test_saving_load_form(client_logged):
    url = reverse('savings:new')

    response = client_logged.get(url)

    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual


@freeze_time('1999-1-1')
def test_saving_save(client_logged):
    a = AccountFactory()
    i = SavingTypeFactory()

    data = {
        'date': '1999-01-01',
        'price': '1.05',
        'fee': '0.25',
        'account': a.pk,
        'saving_type': i.pk
    }

    url = reverse('savings:new')

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert '1999-01-01' in actual
    assert '1,05' in actual
    assert '0,25' in actual
    assert 'Account1' in actual
    assert 'Savings' in actual


def test_saving_save_invalid_data(client_logged):
    data = {
        'date': 'x',
        'price': 'x',
        'fee': 'x',
        'account': 'x',
        'saving_type': 'x'
    }

    url = reverse('savings:new')

    response = client_logged.post(url, data)

    actual = response.context['form']

    assert not actual.is_valid()


@freeze_time('2011-1-1')
def test_saving_update_to_another_year(client_logged):
    saving = SavingFactory()

    data = {
        'price': '150',
        'date': '2010-12-31',
        'remark': 'Pastaba',
        'fee': '25',
        'account': 1,
        'saving_type': 1
    }
    url = reverse('savings:update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert '2010-12-31' not in actual


@freeze_time('1999-12-31')
def test_saving_update(client_logged):
    saving = SavingFactory()

    data = {
        'price': '150',
        'fee': '25',
        'date': '1999-12-31',
        'remark': 'Pastaba',
        'account': 1,
        'saving_type': 1
    }
    url = reverse('savings:update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert '1999-12-31' in actual
    assert '150' in actual
    assert '25' in actual
    assert 'Pastaba' in actual


def test_savings_not_load_other_journal(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(journal=j1, title='a1')
    a2 = AccountFactory(journal=j2, title='a2')

    it1 = SavingTypeFactory(title='xxx', journal=j1)
    it2 = SavingTypeFactory(title='yyy', journal=j2)

    SavingFactory(saving_type=it1, account=a1)
    i2 = SavingFactory(saving_type=it2, account=a2, price=666)

    url = reverse('savings:update', kwargs={'pk': i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
#                                                                           Saving Delete
# ---------------------------------------------------------------------------------------
def test_view_saving_delete_func():
    view = resolve('/savings/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_saving_delete_200(client_logged):
    p = SavingFactory()

    url = reverse('savings:delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_saving_delete_load_form(client_logged):
    p = SavingFactory()

    url = reverse('savings:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)

    form = response.content.decode('utf-8')

    assert '<form method="POST"' in form
    assert f'hx-post="{url}"' in form
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01: Savings</strong>?' in form


def test_view_saving_delete(client_logged):
    p = SavingFactory()

    assert models.Saving.objects.all().count() == 1
    url = reverse('savings:delete', kwargs={'pk': p.pk})

    client_logged.post(url, follow=True)

    assert models.Saving.objects.all().count() == 0


def test_savings_delete_other_journal_get_form(client_logged, second_user):
    it2 = SavingTypeFactory(title='yyy', journal=second_user.journal)
    i2 = SavingFactory(saving_type=it2, price=666)

    url = reverse('savings:delete', kwargs={'pk': i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_delete_other_journal_post_form(client_logged, second_user):
    it2 = SavingTypeFactory(title='yyy', journal=second_user.journal)
    i2 = SavingFactory(saving_type=it2, price=666)

    url = reverse('savings:delete', kwargs={'pk': i2.pk})
    client_logged.post(url, follow=True)

    assert Saving.objects.all().count() == 1


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_type_load_form(client_logged):
    url = reverse('savings:type_new')

    response = client_logged.get(url)

    assert response.status_code == 200


def test_type_save(client_logged):
    data = {
        'title': 'TTT',
        'type': 'funds',
    }

    url = reverse('savings:type_new')

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_type_save_with_closed(client_logged):
    data = {
        'title': 'TTT',
        'closed': '2000',
        'type': 'shares',
    }

    url = reverse('savings:type_new')

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_type_save_invalid_data(client_logged):
    data = {'title': ''}

    url = reverse('savings:type_new')

    response = client_logged.post(url, data, follow=True)

    actual = response.context['form']

    assert not actual.is_valid()


def test_type_update(client_logged):
    saving = SavingTypeFactory()

    data = {
        'title': 'TTT',
        'type': 'funds',
    }
    url = reverse('savings:type_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


def test_type_update_return_list_with_closed(client_logged):
    SavingTypeFactory(title='YYY', closed='1111')
    saving = SavingTypeFactory(title='XXX')

    data = {
        'title': 'TTT',
        'type': 'funds',
    }
    url = reverse('savings:type_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode('utf-8')

    assert 'TTT' in actual
    assert 'YYY' in actual
    assert 'XXX' not in actual


def test_saving_type_not_load_other_journal(client_logged, main_user, second_user):
    SavingTypeFactory(title='xxx', journal=main_user.journal)
    obj = SavingTypeFactory(title='yyy', journal=second_user.journal)

    url = reverse('savings:type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    actual = response.content.decode('utf-8')

    assert obj.title not in actual


def test_type_update_with_closed(client_logged):
    saving = SavingTypeFactory()

    data = {
        'title': 'TTT',
        'closed': '2000',
        'type': 'pensions',
    }
    url = reverse('savings:type_update', kwargs={'pk': saving.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode('utf-8')

    assert 'TTT' in actual


@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get('/savings/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_type_list_view_has_all(client_logged):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1974)

    url = reverse('savings:type_list')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'S1' in actual
    assert 'S2' in actual
