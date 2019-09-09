import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from .. import views

pytestmark = pytest.mark.django_db


def test_index_context_for_accounts(client, login, incomes):
    url = reverse('bookkeeping:index')
    response = client.get(url)

    expect = [{
        'account': 'Account1',
        'past': 5.25,
        'incomes': 3.25,
        'expenses': 0.0,
        'balance': 8.5,
        'have': 0.0,
        'delta': -8.5
    }, {
        'account': 'Account2',
        'past': 4.50,
        'incomes': 3.5,
        'expenses': 0.0,
        'balance': 8.0,
        'have': 0.0,
        'delta': -8.0
    }]

    assert_(expect, response.context['accounts'])


def test_index_context_for_savings(client, login, savings):
    url = reverse('bookkeeping:index')
    response = client.get(url)

    expect = [{
        'saving': 'Saving1',
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
        'saving': 'Saving2',
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

    assert_(expect, response.context['savings'])
