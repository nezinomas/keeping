import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import setup_view
from ...expenses.factories import ExpenseNameFactory, ExpenseTypeFactory
from .. import views

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ---------------------------------------------------------------------------------------
#                                                                        Expenses Summary
# ---------------------------------------------------------------------------------------
def test_summary_func():
    view = resolve('/summary/expenses/')

    assert views.SummaryExpenses is view.func.view_class


def test_summary_200(client_logged):
    url = reverse('bookkeeping:summary_expenses')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_summary_context(client_logged):
    url = reverse('bookkeeping:summary_expenses')
    response = client_logged.get(url)
    context = response.context

    assert 'form' in context

def test_summary_loaded_form(client_logged):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    url = reverse('bookkeeping:summary_expenses')
    response = client_logged.get(url)
    html = response.content.decode('utf-8')

    assert f'<option value="{t.pk}">Expense Type</option>' in html
    assert f'<option value="{t.pk}:{n.pk}">Expense Name</option>' in html


# ---------------------------------------------------------------------------------------
#                                                                   Expenses Summary Data
# ---------------------------------------------------------------------------------------
def test_data_func():
    view = resolve('/summary/expenses/data/')

    assert views.SummaryExpensesData is view.func.view_class


def test_data_200(client_logged):
    url = reverse('bookkeeping:summary_expenses_data')
    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 200


def test_make_form_data_dict(rf):
    class Dummy(views.SummaryExpensesData):
        form_data = '[{"name": "csrf", "value":"xxx"},{"name":"types","value":"1"},{"name":"types","value":"6:6"}]'

    view = setup_view(Dummy(), rf)

    view.make_form_data_dict()

    assert view.form_data_dict['types'] == [1]
    assert view.form_data_dict['names'] == '6'
    assert view.form_data_dict['csrf'] == 'xxx'


def test_make_form_data_dict_extended(rf):
    class Dummy(views.SummaryExpensesData):
        form_data = '[{"name":"types","value":"1"},{"name":"types","value":"6:6"},{"name":"types","value":"2"},{"name":"types","value":"1:7"}]'

    view = setup_view(Dummy(), rf)

    view.make_form_data_dict()

    assert view.form_data_dict['types'] == [1, 2]
    assert view.form_data_dict['names'] == '6,7'
