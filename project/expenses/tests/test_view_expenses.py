import pytest

from ..views import expenses
from .helper_session import add_session_to_request

pytestmark = pytest.mark.django_db


def test_load_expense_name_status_code(rf):
    request = rf.get('/ajax/load_expense_name/?expense_type=1')
    add_session_to_request(request, **{'year': 1999})
    response = expenses.load_expense_name(request)

    assert response.status_code == 200
