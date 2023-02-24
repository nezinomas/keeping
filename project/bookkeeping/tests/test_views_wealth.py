import pytest
from django.urls import resolve, reverse

from ...incomes.factories import IncomeFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve('/bookkeeping/wealth/')

    assert views.Wealth == view.func.view_class


def test_200(client_logged):
    url = reverse('bookkeeping:wealth')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_context(client_logged):
    url = reverse('bookkeeping:wealth')
    response = client_logged.get(url)

    assert 'title' in response.context
    assert 'data' in response.context


def test_content(client_logged):
    IncomeFactory(price=100_000)

    url = reverse('bookkeeping:wealth')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    assert 'Pinigai' in content
    assert 'Turtas' in content
    assert '1.000,00' in content
