import json

import pytest
from django.urls import resolve, reverse

from ...accounts.factories import AccountFactory
from ...core.tests.utils import setup_view
from ...pensions.factories import PensionFactory, PensionTypeFactory
from ...savings.factories import SavingTypeFactory
from .. import views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


#
# ----------------------------------------------------------------------------
#                                                                        Index
# ----------------------------------------------------------------------------
#
def test_view_index_func():
    view = resolve('/')

    assert views.Index == view.func.view_class


@pytest.mark.django_db
def test_view_index_200(login, client):
    response = client.get('/')

    assert response.status_code == 200


#
# ----------------------------------------------------------------------------
#                                                                        Month
# ----------------------------------------------------------------------------
#
def test_view_month_func():
    view = resolve('/month/')

    assert views.Month == view.func.view_class


@pytest.mark.django_db
def test_view_month_200(login, client):
    response = client.get('/month/')

    assert response.status_code == 200


#
# ----------------------------------------------------------------------------
#                                                                Account Worth
# ----------------------------------------------------------------------------
#
def test_view_accounts_worth_func():
    view = resolve('/bookkeeping/accounts_worth/new/')

    assert views.AccountsWorthNew == view.func.view_class


@pytest.mark.django_db
def test_view_account_worth_200(login, client):
    response = client.get('/bookkeeping/accounts_worth/new/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_account_worth_formset(login, client):
    AccountFactory()

    url = reverse('bookkeeping:accounts_worth_new')
    response = client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert 'Sąskaitų vertė' in actual['html_form']
    assert '<option value="1" selected>Account1</option>' in actual['html_form']


@pytest.mark.django_db()
def test_view_account_worth_new(client, login):
    i = AccountFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-account': i.pk
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


@pytest.mark.django_db()
def test_view_account_worth_invalid_data(client, login):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-account': 0
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


#
# ----------------------------------------------------------------------------
#                                                                 Saving Worth
# ----------------------------------------------------------------------------
#
def test_view_savings_worth_func():
    view = resolve('/bookkeeping/savings_worth/new/')

    assert views.SavingsWorthNew == view.func.view_class


@pytest.mark.django_db
def test_view_saving_worth_200(login, client):
    response = client.get('/bookkeeping/savings_worth/new/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_saving_worth_formset(login, client):
    SavingTypeFactory()

    url = reverse('bookkeeping:savings_worth_new')
    response = client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert 'Fondų vertė' in actual['html_form']
    assert '<option value="1" selected>Savings</option>' in actual['html_form']


@pytest.mark.django_db()
def test_view_saving_worth_new(client, login):
    i = SavingTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-saving_type': i.pk
    }

    url = reverse('bookkeeping:savings_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


@pytest.mark.django_db()
def test_view_saving_worth_invalid_data(client, login):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-saving_type': 0
    }

    url = reverse('bookkeeping:savings_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_saving_worth_formset_saving_type_closed_in_past(_fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    _fake_request.user.year = 2000

    view = setup_view(views.SavingsWorthNew(), _fake_request)

    actual = str(view._get_formset())

    assert 'S1' in actual
    assert 'S2' not in actual


@pytest.mark.django_db()
def test_saving_worth_formset_saving_type_closed_in_current(_fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    _fake_request.user.year = 1000

    view = setup_view(views.SavingsWorthNew(), _fake_request)

    actual = str(view._get_formset())

    assert 'S1' in actual
    assert 'S2' in actual


@pytest.mark.django_db()
def test_saving_worth_formset_saving_type_closed_in_future(_fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    _fake_request.user.year = 1

    view = setup_view(views.SavingsWorthNew(), _fake_request)

    actual = str(view._get_formset())

    assert 'S1' in actual
    assert 'S2' in actual


#
# ----------------------------------------------------------------------------
#                                                                Pension Worth
# ----------------------------------------------------------------------------
#
def test_view_pension_worth_func():
    view = resolve('/bookkeeping/pensions_worth/new/')

    assert views.PensionsWorthNew == view.func.view_class


@pytest.mark.django_db
def test_view_pension_worth_200(login, client):
    response = client.get('/bookkeeping/pensions_worth/new/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_pension_worth_formset(login, client):
    PensionFactory()

    url = reverse('bookkeeping:pensions_worth_new')
    response = client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert 'Pensijų vertė' in actual['html_form']
    assert '<option value="1" selected>PensionType</option>' in actual['html_form']


@pytest.mark.django_db()
def test_view_pension_worth_new(client, login):
    i = PensionTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-pension_type': i.pk
    }

    url = reverse('bookkeeping:pensions_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


@pytest.mark.django_db()
def test_view_pension_worth_invalid_data(client, login):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-pension_type': 0
    }

    url = reverse('bookkeeping:pensions_worth_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


#
# ----------------------------------------------------------------------------
#                                                                 Realod Month
# ----------------------------------------------------------------------------
#
def test_view_reload_month_func():
    view = resolve('/month/reload/')

    assert views.reload_month == view.func


@pytest.mark.django_db
def test_view_reload_month_render(login, client):
    url = reverse('bookkeeping:reload_month')
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert views.Month == response.resolver_match.func.view_class


@pytest.mark.django_db
def test_view_reload_month_render_ajax_trigger(login, client):
    url = reverse('bookkeeping:reload_month')
    response = client.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200


#
# ----------------------------------------------------------------------------
#                                                                 Realod Index
# ----------------------------------------------------------------------------
#
def test_view_reload_index_func():
    view = resolve('/bookkeeping/reload/')

    assert views.reload_index == view.func


@pytest.mark.django_db
def test_view_reload_index_render(login, client):
    url = reverse('bookkeeping:reload_index')
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


@pytest.mark.django_db
def test_view_reload_index_render_ajax_trigger(login, client):
    url = reverse('bookkeeping:reload_index')
    response = client.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200


#
# ----------------------------------------------------------------------------
#                                                                     Detailed
# ----------------------------------------------------------------------------
#
def test_view_detailed_func():
    view = resolve('/detailed/')

    assert views.Detailed == view.func.view_class


@pytest.mark.django_db
def test_view_detailed_200(login, client):
    url = reverse('bookkeeping:detailed')
    response = client.get(url)

    assert response.status_code == 200


def test_view_detailed_302(client):
    url = reverse('bookkeeping:detailed')
    response = client.get(url)

    assert response.status_code == 302


@pytest.mark.django_db
def test_view_detailed_rendered_expenses(login, client, expenses):
    url = reverse('bookkeeping:detailed')
    response = client.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Expense Name" in content
    assert "Išlaidos / Expense Type" in content
