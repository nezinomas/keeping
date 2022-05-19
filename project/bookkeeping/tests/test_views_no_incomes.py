import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ...journals.factories import JournalFactory
from ...savings.factories import SavingFactory, SavingTypeFactory
from .. import views
from ..lib.no_incomes import NoIncomes

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                          NoIncomes View
# ---------------------------------------------------------------------------------------
def test_view_func():
    view = resolve('/bookkeeping/no_incomes/')

    assert views.NoIncomes == view.func.view_class


def test_view_200(client_logged):
    url = reverse('bookkeeping:no_incomes')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-07-01')
def test_view(client_logged):
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=1.0,
        expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=2.0,
        expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(
        date=date(1999, 6, 1),
        price=4.0,
        expense_type=ExpenseTypeFactory(title='y'))

    url = reverse('bookkeeping:no_incomes')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 1.17
    assert round(response.context['save_sum'], 2) == 0.0


@freeze_time('1999-07-01')
def test_view_no_data(client_logged):
    url = reverse('bookkeeping:no_incomes')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 0
    assert round(response.context['save_sum'], 2) == 0


def test_view_not_necessary(client_logged):
    j = JournalFactory()
    e1 = ExpenseTypeFactory(title='XXX')
    e2 = ExpenseTypeFactory(title='YYY')
    SavingTypeFactory()

    j.unnecessary_savings = True
    j.unnecessary_expenses = json.dumps([e1.pk, e2.pk])
    j.save()

    url = reverse('bookkeeping:no_incomes')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'Nebūtinos išlaidos, kurių galima atsisakyti:<br />- XXX<br />- YYY<br />- Taupymas' in actual


# ---------------------------------------------------------------------------------------
#                                                                        NoIncomes Helper
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _expenses():
    _x = ExpenseTypeFactory(title='X')
    _y= ExpenseTypeFactory(title='Y')
    _z = ExpenseTypeFactory(title='Z')

    ExpenseFactory(date=date(1998, 12, 1), price=1, expense_type=_x)
    ExpenseFactory(date=date(1998, 12, 1), price=2.6, expense_type=_y)
    ExpenseFactory(date=date(1998, 12, 1), price=3.0, expense_type=_z)

    ExpenseFactory(date=date(1999, 1, 1), price=4, expense_type=_x)
    ExpenseFactory(date=date(1999, 1, 1), price=5.6, expense_type=_y)
    ExpenseFactory(date=date(1999, 1, 1), price=2.0, expense_type=_z)
    ExpenseFactory(date=date(1999, 1, 1), price=4.0, expense_type=_z)


@pytest.fixture
def _savings():
    SavingFactory(date=date(1999, 1, 1), price=2.5)
    SavingFactory(date=date(1999, 1, 1), price=1.5)


@pytest.fixture
def _not_use():
    _z = ExpenseTypeFactory(title='Z')
    return json.dumps([_z.pk])


@freeze_time('1999-2-1')
def test_no_incomes_data(get_user, _not_use, _expenses, _savings):
    get_user.journal.unnecessary_expenses = _not_use
    get_user.journal.unnecessary_savings = True

    obj = NoIncomes(get_user.journal, get_user.year)

    assert obj.avg_expenses == pytest.approx(4.37, rel=1e-2)
    assert obj.cut_sum == pytest.approx(2.17, rel=1e-2)


@freeze_time('1999-2-1')
def test_no_incomes_data_not_use_empty(get_user, _expenses):
    obj = NoIncomes(get_user.journal, get_user.year)

    assert obj.avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert obj.cut_sum == 0.0


@freeze_time('1999-2-1')
def test_no_incomes_data_no_savings(get_user, _not_use, _expenses):
    get_user.journal.unnecessary_expenses = _not_use

    obj = NoIncomes(get_user.journal, get_user.year)

    assert obj.avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert obj.cut_sum == pytest.approx(1.5, rel=1e-2)
