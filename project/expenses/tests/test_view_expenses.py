import pytest
from django.urls import resolve, reverse

from ..models import ExpenseName
from ..views import expenses
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from .helper_session import add_session, add_session_to_request

pytestmark = pytest.mark.django_db


@pytest.fixture()
def db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title='F')
    ExpenseNameFactory(title='S', valid_for=1999)


@pytest.fixture()
def _expenses():
    obj = ExpenseFactory()
    return obj


@pytest.fixture()
def _request(rf):
    def _func(*args, **kwargs):
        request = rf.get('/expenses/')
        add_session_to_request(request, **kwargs)
        return request
    return _func


def test_expenses_items_year_1(_expenses, _request):
    request = _request(**{'year': 1999})
    items = expenses._items(request)

    assert 1 == len(items)


def test_expenses_items_year_2(_expenses, _request):
    request = _request(**{'year': 1970})
    items = expenses._items(request)

    assert 0 == len(items)


def test_load_expense_name_status_code(client):
    add_session(client, **{'year': 1999})

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client, db_data):
    add_session(client, **{'year': 1})

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 1 == response.context['objects'].count()


def test_load_expense_name_all(client, db_data):
    add_session(client, **{'year': 1999})

    url = reverse('expenses:load_expense_name')
    response = client.get(url, {'expense_type': 1})

    assert 2 == response.context['objects'].count()
