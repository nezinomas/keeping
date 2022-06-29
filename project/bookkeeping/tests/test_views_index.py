from datetime import date
from freezegun import freeze_time

import pytest
from django.urls import resolve, reverse

from ...debts.factories import BorrowFactory, LendFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...pensions.factories import PensionFactory
from ...savings.factories import SavingFactory
from .. import views
from ..services.index import IndexService

pytestmark = pytest.mark.django_db


def test_view_index_func():
    view = resolve('/')

    assert views.Index == view.func.view_class


def test_view_index_200(client_logged):
    response = client_logged.get('/')

    assert response.status_code == 200


def test_view_index_context(client_logged):
    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert 'year' in response.context
    assert 'accounts' in response.context
    assert 'savings' in response.context
    assert 'pensions' in response.context
    assert 'wealth' in response.context
    assert 'no_incomes' in response.context
    assert 'balance' in response.context
    assert 'balance_short' in response.context
    assert 'expenses' in response.context
    assert 'averages' in response.context
    assert 'borrow' in response.context
    assert 'lend' in response.context
    assert 'chart_expenses' in response.context
    assert 'chart_balance' in response.context


def test_view_index_regenerate_buttons(client_logged):
    SavingFactory()
    PensionFactory()

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    url = reverse('core:regenerate_balances')

    assert f'hx-get="{ url }"' in content
    assert f'hx-get="{ url }?type=accounts"' in content
    assert f'hx-get="{ url }?type=savings"' in content
    assert f'hx-get="{ url }?type=pensions"' in content

    assert 'Bus atnaujinti visų metų balansai.' in content
    assert 'Bus atnaujinti tik šios lentelės balansai.' in content
    assert content.count('Bus atnaujinti tik šios lentelės balansai.') == 3


# ---------------------------------------------------------------------------------------
#                                                                            Index Helper
# ---------------------------------------------------------------------------------------
def test_render_borrow_no_data(rf):
    obj = IndexService(rf, 1999)
    actual = obj.render_borrow()

    assert not actual


def test_render_borrow(rf):
    BorrowFactory()

    obj = IndexService(rf, 1999)
    actual = obj.render_borrow()

    assert 'Pasiskolinta' in actual['title']
    assert 'Grąžinau' in actual['title']
    assert  actual['data'] == [100.0, 0.0]


def test_render_lend_no_data(rf):
    obj = IndexService(rf, 1999)
    actual = obj.render_lend()

    assert not actual


def test_render_lend(rf):
    LendFactory()
    obj = IndexService(rf, 1999)
    actual = obj.render_lend()

    assert 'Paskolinta' in actual['title']
    assert 'Grąžino' in actual['title']
    assert actual['data'] == [100.0, 0.0]


@freeze_time('1999-1-1')
def test_render_year_balance_short(rf):
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=25)
    SavingFactory(price=10)

    obj = IndexService(rf, 1999).render_year_balance_short()

    assert obj['title'] == ['Metų pradžioje', 'Metų pabaigoje', 'Metų balansas']
    assert obj['data'] == [5.0, 70.0, 65.0]


def test_render_year_balance_short_highlight_balance(rf):
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=125)

    obj = IndexService(rf, 1999).render_year_balance_short()

    assert obj['data'] == [5.0, -20.0, -25.0]
    assert obj['highlight'] == [False, False, True]
