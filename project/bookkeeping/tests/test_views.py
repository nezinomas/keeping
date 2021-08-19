import json
from datetime import date, datetime
from decimal import Decimal

import pytest
import pytz
from django.http import JsonResponse
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...core.tests.utils import setup_view
from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from ...pensions.factories import (PensionBalanceFactory, PensionFactory,
                                   PensionTypeFactory)
from ...savings.factories import SavingBalanceFactory, SavingTypeFactory
from .. import models, views
from ..factories import (AccountWorthFactory, PensionWorthFactory,
                         SavingWorthFactory)

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ---------------------------------------------------------------------------------------
#                                                                                   Index
# ---------------------------------------------------------------------------------------
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
    assert 'year_balance' in response.context
    assert 'year_balance_short' in response.context
    assert 'year_expenses' in response.context
    assert 'no_incomes' in response.context
    assert 'averages' in response.context
    assert 'wealth' in response.context
    assert 'borrow' in response.context
    assert 'lent' in response.context
    assert 'chart_expenses' in response.context
    assert 'chart_balance' in response.context


@freeze_time('1999-07-01')
def test_no_incomes(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=1.0, expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(date=date(1999, 1, 1), price=2.0, expense_type=ExpenseTypeFactory(title='Darbas'))
    ExpenseFactory(date=date(1999, 6, 1), price=4.0, expense_type=ExpenseTypeFactory(title='y'))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 1.17
    assert round(response.context['save_sum'], 2) == 0.0


@freeze_time('1999-07-01')
def test_no_incomes_no_data(client_logged):
    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    assert round(response.context['avg_expenses'], 2) == 0
    assert round(response.context['save_sum'], 2) == 0


def test_index_account_worth(client_logged):
    AccountBalanceFactory()
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(2222, 2, 2, tzinfo=pytz.utc))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = response.context['accounts'][0]

    assert exp['latest_check'] == datetime(2222, 2, 2, tzinfo=pytz.utc)


def test_index_account_worth_then_last_check_empty(client_logged):
    AccountBalanceFactory()

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = response.context['accounts'][0]

    assert exp['latest_check'] == None


def test_index_savings_worth(client_logged):
    SavingBalanceFactory()
    SavingWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    SavingWorthFactory(date=datetime(2222, 2, 2, tzinfo=pytz.utc))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = [x['items'] for x in response.context if x.get('title') == 'Fondai'][0][0]

    assert exp['latest_check'] == datetime(2222, 2, 2, tzinfo=pytz.utc)


def test_index_pension_worth(client_logged):
    PensionBalanceFactory()
    PensionWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    PensionWorthFactory(date=datetime(2222, 2, 2, tzinfo=pytz.utc))

    url = reverse('bookkeeping:index')
    response = client_logged.get(url)

    exp = [x['items'] for x in response.context if x.get('title') == 'Pensijos'][0][0]

    assert exp['latest_check'] == datetime(2222, 2, 2, tzinfo=pytz.utc)


# ---------------------------------------------------------------------------------------
#                                                                                   Month
# ---------------------------------------------------------------------------------------
def test_view_month_func():
    view = resolve('/month/')

    assert views.Month == view.func.view_class


def test_view_month_200(client_logged):
    response = client_logged.get('/month/')

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                          Month Day List
# ---------------------------------------------------------------------------------------
def test_view_expand_day_expenses_func():
    view = resolve('/month/11112233/')

    assert views.ExpandDayExpenses == view.func.view_class


def test_view_expand_day_expenses_200(client_logged):
    response = client_logged.get('/month/')

    assert response.status_code == 200


@pytest.mark.xfail
def test_view_expand_day_expenses_str_in_url(client_logged):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': 'xx'})
    client_logged.get(url)


@pytest.mark.parametrize(
    'dt, expect',
    [
        ('19701301', '1970-01-01 dieną įrašų nėra'),
        ('19701232', '1970-01-01 dieną įrašų nėra'),
    ]
)
def test_view_expand_day_expenses_wrong_dates(dt, expect, client_logged):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': dt})
    response = client_logged.get(url)

    actual = json.loads(response.content)

    assert expect in actual['html']


def test_view_expand_day_expenses_302(client):
    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': '19700101'})
    response = client.get(url)

    assert response.status_code == 302


def test_view_expand_day_expenses_ajax(client_logged):
    ExpenseFactory()

    url = reverse('bookkeeping:expand_day_expenses', kwargs={'date': '19990101'})
    response = client_logged.get(url, {}, **X_Req)

    actual = json.loads(response.content)

    assert response.status_code == 200
    assert '1999-01-01' in actual['html']
    assert 'Expense Type' in actual['html']
    assert 'Expense Name' in actual['html']


# ---------------------------------------------------------------------------------------
#                                                                           Account Worth
# ---------------------------------------------------------------------------------------
def test_accounts_worth_func():
    view = resolve('/bookkeeping/accounts_worth/new/')

    assert views.AccountsWorthNew == view.func.view_class


def test_account_worth_200(client_logged):
    response = client_logged.get('/bookkeeping/accounts_worth/new/')

    assert response.status_code == 200


def test_account_worth_formset(client_logged):
    AccountFactory()

    url = reverse('bookkeeping:accounts_worth_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert 'Sąskaitų vertė' in actual['html_form']
    assert '<option value="1" selected>Account1</option>' in actual['html_form']


@freeze_time('1999-9-9')
def test_account_worth_new(client_logged):
    i = AccountFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-account': i.pk
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']
    assert 'data-bs-title="1999 m. rugsėjo 9 d.' in actual['html_list']

def test_account_worth_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-account': 0
    }

    url = reverse('bookkeeping:accounts_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_account_worth_formset_closed_in_past(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 2000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  # pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' not in actual


def test_account_worth_formset_closed_in_current(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1000

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


def test_account_worth_formset_closed_in_future(get_user, fake_request):
    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=1000)

    get_user.year = 1

    view = setup_view(views.AccountsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


# ---------------------------------------------------------------------------------------
#                                                                     Account Worth Reset
# ---------------------------------------------------------------------------------------
def test_account_worth_reset_func():
    view = resolve('/bookkeeping/accounts_worth/reset/1/')

    assert views.AccountsWorthReset == view.func.view_class


def test_account_worth_reset_200(client_logged):
    a = AccountWorthFactory()
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_account_worth_reset_302(client):
    a = AccountWorthFactory()
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.pk})
    response = client.get(url)

    assert response.status_code == 302


def test_account_worth_reset_404(client_logged):
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': 1})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_account_worth_reset_string_404(client_logged):
    url = '/bookkeeping/accounts_worth/reset/x/'
    response = client_logged.get(url)

    assert response.status_code == 404


def test_account_worth_reset_already_reseted(client_logged):
    a = AccountWorthFactory(price=0)

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.account.pk})
    response = client_logged.get(url)

    assert response.status_code == 204


def test_account_worth_reset(client_logged):
    a = AccountWorthFactory()

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.account.pk})
    client_logged.get(url)

    actual = models.AccountWorth.objects.last()

    assert actual.price == Decimal(0.0)

    actual = models.AccountWorth.objects.all()

    assert actual.count() == 2


def test_account_worth_reset_no_object(client_logged):
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': 1})
    client_logged.get(url)

    actual = models.AccountWorth.objects.all()

    assert actual.count() == 0


# ---------------------------------------------------------------------------------------
#                                                                            Saving Worth
# ---------------------------------------------------------------------------------------
def test_view_savings_worth_func():
    view = resolve('/bookkeeping/savings_worth/new/')

    assert views.SavingsWorthNew == view.func.view_class


def test_view_saving_worth_200(client_logged):
    response = client_logged.get('/bookkeeping/savings_worth/new/')

    assert response.status_code == 200


def test_view_saving_worth_formset(client_logged):
    SavingTypeFactory()

    url = reverse('bookkeeping:savings_worth_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert 'Fondų vertė' in actual['html_form']
    assert '<option value="1" selected>Savings</option>' in actual['html_form']


def test_view_saving_worth_new(client_logged):
    i = SavingTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-saving_type': i.pk
    }

    url = reverse('bookkeeping:savings_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert not actual.get('html_list')


def test_view_saving_worth_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-saving_type': 0
    }

    url = reverse('bookkeeping:savings_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_saving_worth_formset_saving_type_closed_in_past(get_user, fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    get_user.year = 2000

    view = setup_view(views.SavingsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' not in actual


def test_saving_worth_formset_saving_type_closed_in_current(get_user, fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    get_user.year = 1000

    view = setup_view(views.SavingsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


def test_saving_worth_formset_saving_type_closed_in_future(get_user, fake_request):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=1000)

    get_user.year = 1

    view = setup_view(views.SavingsWorthNew(), fake_request)

    actual = str(view._get_formset())  #pylint: disable=protected-access

    assert 'S1' in actual
    assert 'S2' in actual


# ---------------------------------------------------------------------------------------
#                                                                           Pension Worth
# ---------------------------------------------------------------------------------------
def test_view_pension_worth_func():
    view = resolve('/bookkeeping/pensions_worth/new/')

    assert views.PensionsWorthNew == view.func.view_class


def test_view_pension_worth_200(client_logged):
    response = client_logged.get('/bookkeeping/pensions_worth/new/')

    assert response.status_code == 200


def test_view_pension_worth_formset(client_logged):
    PensionFactory()

    url = reverse('bookkeeping:pensions_worth_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert 'Pensijų vertė' in actual['html_form']
    assert '<option value="1" selected>PensionType</option>' in actual['html_form']


def test_view_pension_worth_new(client_logged):
    i = PensionTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': '999',
        'form-0-pension_type': i.pk
    }

    url = reverse('bookkeeping:pensions_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_pension_worth_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-price': 'x',
        'form-0-pension_type': 0
    }

    url = reverse('bookkeeping:pensions_worth_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


# ---------------------------------------------------------------------------------------
#                                                                            Realod Month
# ---------------------------------------------------------------------------------------
def test_view_reload_month_func():
    view = resolve('/month/reload/')

    assert views.ReloadMonth is view.func.view_class


def test_view_reload_month_render(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Month == response.resolver_match.func.view_class


def test_view_reload_month_render_ajax_trigger(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200

    actual = json.loads(response.content)

    assert len(actual) == 4
    assert 'month_table' in actual
    assert 'info' in actual
    assert 'chart_expenses' in actual
    assert 'chart_targets' in actual


def test_view_reload_month_return_object(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)


# ---------------------------------------------------------------------------------------
#                                                                            Realod Index
# ---------------------------------------------------------------------------------------
def test_view_reload_index_func():
    view = resolve('/bookkeeping/reload/')

    assert views.ReloadIndex is view.func.view_class


def test_view_reload_index_render(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_view_reload_index_return_object(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)


def test_view_reload_index_render_ajax_trigger(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert len(actual) == 3
    assert 'no_incomes' in actual
    assert 'wealth' in actual
    assert 'savings' in actual


# ---------------------------------------------------------------------------------------
#                                                                                Detailed
# ---------------------------------------------------------------------------------------
def test_view_detailed_func():
    view = resolve('/detailed/')

    assert views.Detailed == view.func.view_class


def test_view_detailed_200(client_logged):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_detailed_302(client):
    url = reverse('bookkeeping:detailed')
    response = client.get(url)

    assert response.status_code == 302


def test_view_detailed_rendered_expenses(client_logged, expenses):
    url = reverse('bookkeeping:detailed')
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Expense Name" in content
    assert "Išlaidos / Expense Type" in content


# ---------------------------------------------------------------------------------------
#                                                                                 Summary
# ---------------------------------------------------------------------------------------
def test_view_summary_func():
    view = resolve('/summary/')

    assert views.Summary == view.func.view_class


def test_view_summary_200(client_logged):
    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.status_code == 200


@freeze_time('1999-01-01')
def test_view_summary_salary_avg(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_data_avg'] == [1.0, 10.0]


@freeze_time('1999-01-01')
def test_view_summary_salary_years(client_logged):
    IncomeFactory(date=date(1998, 1, 1), price=12.0, income_type=IncomeTypeFactory(title='Atlyginimas'))
    IncomeFactory(date=date(1999, 1, 1), price=10.0, income_type=IncomeTypeFactory(title='Atlyginimas'))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['salary_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_view_summary_balance_years(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
def test_view_summary_incomes_avg(client_logged):
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1998, 1, 1),
        price=12.0,
        income_type=IncomeTypeFactory(title='Kita')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=10.0,
        income_type=IncomeTypeFactory(title='Atlyginimas')
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=2.0,
        income_type=IncomeTypeFactory(title='Kt')
    )

    url = reverse('bookkeeping:summary')
    response = client_logged.get(url)

    assert response.context['balance_income_avg'] == [2.0, 12.0]
