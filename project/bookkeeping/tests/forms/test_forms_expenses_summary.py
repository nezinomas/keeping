import pytest

from ....expenses.tests.factories import ExpenseNameFactory, ExpenseTypeFactory
from ...forms import SummaryExpensesForm

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                 Summary Expenses Form
# -------------------------------------------------------------------------------------
def test_form_init(main_user):
    SummaryExpensesForm(user=main_user)


def test_form_fields(main_user):
    form = SummaryExpensesForm(user=main_user).as_p()

    assert '<select name="types"' in form


def test_form_load(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    form = SummaryExpensesForm(user=main_user).as_p()

    assert f'<option value="{t.pk}">Expense Type</option>' in form
    assert f'<option value="{t.pk}:{n.pk}">Expense Name</option>' in form


def test_form_empty_error(main_user):
    form = SummaryExpensesForm(user=main_user, data={"types": [], "names": []})

    assert not form.is_valid()
    assert form.errors["__all__"] == ["Reikia pasirinkti bent vieną kategoriją."]
