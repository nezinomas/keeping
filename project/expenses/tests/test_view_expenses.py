import pytest
from django.urls import resolve, reverse

from ..models import ExpenseName
from ..views import expenses
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title='F')
    ExpenseNameFactory(title='S', valid_for=1999)


def _change_profile_year(client):
    url = reverse('core:core_index')
    response = client.get(url)

    u = response.wsgi_request.user
    u.profile.year = 1
    u.save()


def test_load_expense_name_status_code(client, login):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client, login, db_data):
    _change_profile_year(client)

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 1 == response.context['objects'].count()


def test_load_expense_name_all(client, login, db_data):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 2 == response.context['objects'].count()
