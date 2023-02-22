from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse
from ...pensions.factories import PensionFactory
from .. import views
from ..factories import PensionWorthFactory

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve('/bookkeeping/pensions/')

    assert views.Pensions == view.func.view_class


def test_view_200(client_logged):
    url = reverse('bookkeeping:pensions')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context(client_logged):
    url = reverse('bookkeeping:pensions')
    response = client_logged.get(url)
    actual = response.context

    assert actual['title'] == 'Pensijos'
    assert actual['type'] == 'pensions'
    assert 'items' in actual
    assert 'total_row' in actual


def test_view_latest_check(client_logged):
    PensionFactory()
    PensionWorthFactory()
    PensionWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = [x['items']
           for x in response.context if x.get('title') == 'Pensijos'][0][0]

    assert exp.latest_check == datetime(1999, 1, 1, 1, 3, 4, tzinfo=pytz.utc)
