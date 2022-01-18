import pytest
from django.urls import resolve, reverse

from ...savings.factories import SavingFactory
from .. import views

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                         Savings Summary
# ---------------------------------------------------------------------------------------
def test_view_summary_savings_func():
    view = resolve('/summary/savings/')

    assert views.SummarySavings == view.func.view_class


def test_view_summary_savings_200(client_logged):
    url = reverse('bookkeeping:summary_savings')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_summery_savings_context(client_logged):
    SavingFactory(price=111)

    url = reverse('bookkeeping:summary_savings')
    response = client_logged.get(url)

    assert 'records' in response.context
    assert 'funds' in response.context
    assert 'shares' in response.context
    assert 'pensions2' in response.context
    assert 'pensions3' in response.context
    assert 'all' in response.context

    assert response.context['funds']['categories'] == [1999]
    assert response.context['funds']['invested'] == [111.0]
    assert response.context['funds']['profit'] == [0.0]


def test_view_summery_savings_context_no_records(client_logged):
    url = reverse('bookkeeping:summary_savings')
    response = client_logged.get(url)

    assert 'records' in response.context
    assert 'funds' not in response.context
    assert 'shares' not in response.context
    assert 'pensions2' not in response.context
    assert 'pensions3' not in response.context
    assert 'all' not in response.context

    assert response.context['records'] == 0
