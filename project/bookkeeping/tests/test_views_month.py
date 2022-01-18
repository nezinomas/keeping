import json

import pytest
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseFactory
from .. import views

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ---------------------------------------------------------------------------------------
#                                                                                   Month
# ---------------------------------------------------------------------------------------
def test_view_month_func():
    view = resolve('/month/')

    assert views.Month == view.func.view_class


def test_view_month_200(client_logged):
    response = client_logged.get('/month/')

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                          Month Day List
# ---------------------------------------------------------------------------------------
def test_view_expand_day_expenses_func():
    view = resolve('/month/11112233/')

    assert views.ExpandDayExpenses == view.func.view_class


def test_view_expand_day_expenses_200(client_logged):
    response = client_logged.get('/month/')

    assert response.status_code == 200


@pytest.mark.xfail
def test_view_expand_day_expenses_str_in_url(client_logged):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': 'xx'})
    client_logged.get(url)


@pytest.mark.parametrize(
    'dt, expect',
    [
        ('19701301', '1970-01-01 dieną įrašų nėra'),
        ('19701232', '1970-01-01 dieną įrašų nėra'),
    ]
)
def test_view_expand_day_expenses_wrong_dates(dt, expect, client_logged):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': dt})
    response = client_logged.get(url)

    actual = json.loads(response.content)

    assert expect in actual['html']


def test_view_expand_day_expenses_302(client):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': '19700101'})
    response = client.get(url)

    assert response.status_code == 302


def test_view_expand_day_expenses_ajax(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': '19990101'})
    response = client_logged.get(url, {}, **X_Req)

    actual = json.loads(response.content)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html']
    assert 'Expense Type' in actual['html']
    assert 'Expense Name' in actual['html']
