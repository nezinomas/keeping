import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import change_profile_year
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..models import ExpenseName
from ..views import expenses

pytestmark = pytest.mark.django_db


@pytest.fixture()
def db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title='F')
    ExpenseNameFactory(title='S', valid_for=1999)


def test_load_expense_name_status_code(client, login):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client, login, db_data):
    change_profile_year(client)

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 1 == response.context['objects'].count()


def test_load_expense_name_all(client, login, db_data):
    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 2 == response.context['objects'].count()
