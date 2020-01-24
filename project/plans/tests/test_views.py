import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from .. import models, views
from ..factories import (
    DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
    NecessaryPlanFactory, SavingPlanFactory)

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ----------------------------------------------------------------------------
#                                                                   Index Plan
# ----------------------------------------------------------------------------
def test_view_index(client_logged):
    url = reverse('plans:plans_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_index_not_logged(client):
    url = reverse('plans:plans_index')
    response = client.get(url)

    # redirection to login page
    assert response.status_code == 302


def test_view_index_func(client):
    view = resolve('/plans/')

    assert views.Index == view.func.view_class


# ----------------------------------------------------------------------------
#                                                                  plans_stats
# ----------------------------------------------------------------------------
def test_view_plan_stats_render(client_logged):
    url = reverse('plans:reload_plan_stats')

    response = client_logged.get(url, {'ajax_trigger': True})

    assert response.status_code == 200


def test_view_plan_stats_render_to_string(client_logged):
    url = reverse('plans:reload_plan_stats')

    response = client_logged.get(url, {'ajax_trigger': False})

    assert response.status_code == 200


# ----------------------------------------------------------------------------
#                                                     IncomePlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_incomes(get_user, client_logged):
    url = reverse('plans:incomes_plan_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_incomes_new(client_logged):
    i = IncomeTypeFactory()
    data = {'year': '1999', 'income_type': i.pk, 'january': 999.99}

    url = reverse('plans:incomes_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_incomes_new_invalid_data(client_logged):
    data = {'year': 'x', 'income_type': 0, 'january': 999.99}

    url = reverse('plans:incomes_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_incomes_update(client_logged):
    p = IncomePlanFactory(year=1999)

    data = {'year': '1999', 'income_type': p.income_type.pk, 'january': 999.99}
    url = reverse('plans:incomes_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_incomes_update_unique_together_user_change_year(client_logged):
    IncomePlanFactory(year=2000)
    p = IncomePlanFactory(year=1999)

    data = {'year': '2000', 'income_type': p.income_type.pk, 'january': 999.99}
    url = reverse('plans:incomes_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_incomes_update_year_not_match(client_logged):
    # if year in Plan and user not match, 404 error
    p = IncomePlanFactory(year=2000)

    url = reverse('plans:incomes_plan_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 404


# ----------------------------------------------------------------------------
#                                                            IncomePlan delete
# ----------------------------------------------------------------------------
def test_view_incomes_delete_func():
    view = resolve('/plans/incomes/delete/1/')

    assert views.IncomesDelete == view.func.view_class


def test_view_incomes_delete_200(client_logged):
    p = IncomePlanFactory()

    url = reverse('plans:incomes_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_incomes_delete_load_form(client_logged):
    p = IncomePlanFactory(year=1999)

    url = reverse('plans:incomes_plan_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/plans/incomes/delete/1/"' in actual['html_form']


def test_view_incomes_delete(client_logged):
    p = IncomePlanFactory(year=1999)

    assert models.IncomePlan.objects.all().count() == 1
    url = reverse('plans:incomes_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.IncomePlan.objects.all().count() == 0


# ----------------------------------------------------------------------------
#                                                   ExpensesPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_expenses(client_logged):
    url = reverse('plans:expenses_plan_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_expenses_new(client_logged):
    i = ExpenseTypeFactory()
    data = {'year': '1999', 'expense_type': i.pk, 'january': 999.99}

    url = reverse('plans:expenses_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_expenses_new_invalid_data(client_logged):
    data = {'year': 'x', 'expense_type': 0, 'january': 999.99}

    url = reverse('plans:expenses_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_expenses_update(client_logged):
    p = ExpensePlanFactory(year=1999)

    data = {'year': '1999', 'expense_type': p.expense_type.pk, 'january': 999.99}
    url = reverse('plans:expenses_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_expenses_update_unique_together_user_change_year(client_logged):
    ExpensePlanFactory(year=2000)
    p = ExpensePlanFactory(year=1999)

    data = {'year': '2000', 'expense_type': p.expense_type.pk, 'january': 999.99}
    url = reverse('plans:expenses_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_expenses_update_year_not_match(client_logged):
    # if year in Plan and urser. not match, 404 error
    p = ExpensePlanFactory(year=1974)

    url = reverse('plans:expenses_plan_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 404


# ----------------------------------------------------------------------------
#                                                          ExpensesPlan delete
# ----------------------------------------------------------------------------
def test_view_expenses_delete_func():
    view = resolve('/plans/expenses/delete/1/')

    assert views.ExpensesDelete == view.func.view_class


def test_view_expenses_delete_200(client_logged):
    p = ExpensePlanFactory()

    url = reverse('plans:expenses_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_expenses_delete_load_form(client_logged):
    p = ExpensePlanFactory(year=1999)

    url = reverse('plans:expenses_plan_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/plans/expenses/delete/1/"' in actual['html_form']


def test_view_expenses_delete(client_logged):
    p = ExpensePlanFactory(year=1999)

    assert models.ExpensePlan.objects.all().count() == 1
    url = reverse('plans:expenses_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.ExpensePlan.objects.all().count() == 0


# ----------------------------------------------------------------------------
#                                                     SavingPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_savings(client_logged):
    url = reverse('plans:savings_plan_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_savings_new(client_logged):
    i = SavingTypeFactory()
    data = {'year': '1999', 'saving_type': i.pk, 'january': 999.99}

    url = reverse('plans:savings_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_savings_new_invalid_data(client_logged):
    data = {'year': 'x', 'saving_type': 0, 'january': 999.99}

    url = reverse('plans:savings_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_savings_update(client_logged):
    p = SavingPlanFactory(year=1999)

    data = {'year': '1999', 'saving_type': p.saving_type.pk, 'january': 999.99}
    url = reverse('plans:savings_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_savings_update_unique_together_user_change_year(client_logged):
    SavingPlanFactory(year=2000)
    p = SavingPlanFactory(year=1999)

    data = {'year': '2000', 'saving_type': p.saving_type.pk, 'january': 999.99}
    url = reverse('plans:savings_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_savings_update_year_not_match(client_logged):
    # if year in Plan and urser not match, 404 error
    p = SavingPlanFactory(year=1974)

    url = reverse('plans:savings_plan_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 404


# ----------------------------------------------------------------------------
#                                                            SavingPlan delete
# ----------------------------------------------------------------------------
def test_view_savings_delete_func():
    view = resolve('/plans/savings/delete/1/')

    assert views.SavingsDelete == view.func.view_class


def test_view_savings_delete_200(client_logged):
    p = SavingPlanFactory()

    url = reverse('plans:savings_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_savings_delete_load_form(client_logged):
    p = SavingPlanFactory(year=1999)

    url = reverse('plans:savings_plan_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/plans/savings/delete/1/"' in actual['html_form']


def test_view_savings_delete(client_logged):
    p = SavingPlanFactory(year=1999)

    assert models.SavingPlan.objects.all().count() == 1
    url = reverse('plans:savings_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.SavingPlan.objects.all().count() == 0


# ----------------------------------------------------------------------------
#                                                        DayPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_days(client_logged):
    url = reverse('plans:days_plan_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_days_new(client_logged):
    data = {'year': '1999', 'january': 999.99}

    url = reverse('plans:days_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_days_new_invalid_data(client_logged):
    data = {'year': 'x', 'january': 999.99}

    url = reverse('plans:days_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_days_update(client_logged):
    p = DayPlanFactory(year=1999)

    data = {'year': '1999', 'january': 999.99}
    url = reverse('plans:days_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_days_update_unique_together_user_change_year(client_logged):
    DayPlanFactory(year=2000)
    p = DayPlanFactory(year=1999)

    data = {'year': '2000', 'january': 999.99}
    url = reverse('plans:days_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_days_update_year_not_match(client_logged):
    # if year in Plan and urser not match, 404 error
    p = DayPlanFactory(year=1974)

    url = reverse('plans:days_plan_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 404


# ----------------------------------------------------------------------------
#                                                               DayPlan delete
# ----------------------------------------------------------------------------
def test_view_days_delete_func():
    view = resolve('/plans/day/delete/1/')

    assert views.DayDelete == view.func.view_class


def test_view_days_delete_200(client_logged):
    p = DayPlanFactory()

    url = reverse('plans:days_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_days_delete_load_form(client_logged):
    p = DayPlanFactory(year=1999)

    url = reverse('plans:days_plan_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<form method="post"' in actual['html_form']
    assert 'action="/plans/day/delete/1/"' in actual['html_form']


def test_view_days_delete(client_logged):
    p = DayPlanFactory(year=1999)

    assert models.DayPlan.objects.all().count() == 1
    url = reverse('plans:days_plan_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.DayPlan.objects.all().count() == 0


# ----------------------------------------------------------------------------
#                                                  NecessaryPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_necessarys(client_logged):
    url = reverse('plans:necessarys_plan_new')
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_necessarys_new(client_logged):
    data = {'year': '1999', 'title': 'X', 'january': 999.99}

    url = reverse('plans:necessarys_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_necessarys_new_invalid_data(client_logged):
    data = {'year': 'x', 'title': '', 'january': 999.99}

    url = reverse('plans:necessarys_plan_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_necessarys_update(client_logged):
    p = NecessaryPlanFactory(year=1999)

    data = {'year': '1999', 'title': 'X', 'january': 999.99}
    url = reverse('plans:necessarys_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


def test_view_necessarys_update_unique_together_user_change_year(client_logged):
    NecessaryPlanFactory(year=2000, title='XXX')
    p = NecessaryPlanFactory(year=1999, title='XXX')

    data = {'year': '2000', 'title': 'XXX', 'january': 999.99}
    url = reverse('plans:necessarys_plan_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_necessarys_update_year_not_match(client_logged):
    # if year in Plan and urser not match, 404 error
    p = NecessaryPlanFactory(year=1974)

    url = reverse('plans:necessarys_plan_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, {}, **X_Req)

    assert response.status_code == 404


# ----------------------------------------------------------------------------
#                                                                   Copy Plans
# ----------------------------------------------------------------------------
def test_copy_func():
    view = resolve('/plans/copy/')

    assert views.copy_plans == view.func


@pytest.mark.django_db
def test_copy_200(client_logged):
    response = client_logged.get('/plans/copy/')

    assert response.status_code == 200


def test_copy_success(get_user, client_logged):
    IncomePlanFactory(year=1999)
    data = {'year_from': '1999', 'year_to': '2000', 'income': True}

    url = reverse('plans:copy_plans')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    data = models.IncomePlan.objects.year(2000)

    assert data.exists()
    assert data[0].year == 2000


def test_copy_fails(client_logged):
    data = {'year_from': '1999', 'year_to': '2000', 'income': True}

    url = reverse('plans:copy_plans')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']
