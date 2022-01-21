import pytest

from ...expenses.factories import ExpenseNameFactory, ExpenseTypeFactory
from ..forms import SummaryExpensesForm

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                   Summary Expenses Form
# ---------------------------------------------------------------------------------------
def test_form_init():
    SummaryExpensesForm()


def test_form_fields():
    form = SummaryExpensesForm().as_p()

    assert '<select name="types"' in form
    assert '<input type="hidden" name="names"' in form


def test_form_load():
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    form = SummaryExpensesForm().as_p()

    assert f'<option value="{t.pk}">Expense Type</option>' in form
    assert f'<option value="{t.pk}:{n.pk}">Expense Name</option>' in form


def test_form_empty_error():
    form = SummaryExpensesForm(data={'types':[], 'names':[]})

    assert not form.is_valid()
    assert form.errors['__all__'] == ['Reikia pasirinkti bent vieną kategoriją.']
