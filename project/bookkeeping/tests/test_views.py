import json

import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...savings.factories import SavingTypeFactory
from .. import views
from ...accounts.factories import AccountFactory


X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


@pytest.mark.django_db()
def test_index_context_for_accounts(
    client, login,
    incomes, expenses, savings, transactions,
    savings_close, accounts_worth
):
    url = reverse('bookkeeping:index')
    response = client.get(url)

    expect = [{
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
        'have': 3.25,
        'delta': -0.75
    }, {
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
        'have': 8.0,
        'delta': 8.75
    }]

    assert_(expect, response.context['accounts'])


@pytest.mark.django_db()
def test_index_context_for_savings(client, login, savings):
    url = reverse('bookkeeping:index')
    response = client.get(url)

    expect = [{
        'title': 'Saving1',
        'past_amount': 1.25,
        'past_fee': 0.25,
        'incomes': 4.75,
        'fees': 0.75,
        'invested': 4.0,
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'title': 'Saving2',
        'past_amount': 0.25,
        'past_fee': 0.0,
        'incomes': 2.50,
        'fees': 0.25,
        'invested': 2.25,
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    assert_(expect, response.context['fund'])


def test_view_index_func():
    view = resolve('/')

    assert views.Index == view.func.view_class


def test_view_month_func():
    view = resolve('/month/')

    assert views.Month == view.func.view_class


def test_view_savings_worth_func():
    view = resolve('/bookkeeping/savings_worth/new/')

    assert views.SavingsWorthNew == view.func.view_class


def test_view_accounts_worth_func():
    view = resolve('/bookkeeping/accounts_worth/new/')

    assert views.AccountsWorthNew == view.func.view_class


@pytest.mark.django_db
def test_view_index_200(login, client):
    response = client.get('/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_month_200(login, client):
    response = client.get('/month/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_saving_worth_200(login, client):
    response = client.get('/bookkeeping/savings_worth/new/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_account_worth_200(login, client):
    response = client.get('/bookkeeping/accounts_worth/new/')

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
