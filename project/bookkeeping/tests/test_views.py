import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from .. import views


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
