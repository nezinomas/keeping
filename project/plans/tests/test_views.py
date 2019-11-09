import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ..factories import (
    DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
    NecessaryPlanFactory, SavingPlanFactory)
from ..views import Index

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


# ----------------------------------------------------------------------------
#                                                                   Index Plan
# ----------------------------------------------------------------------------
@pytest.mark.django_db()
def test_view_index(client, login):
    url = reverse('plans:plans_index')
    response = client.get(url)

    assert 200 == response.status_code


@pytest.mark.django_db()
def test_view_index_not_logged(client):
    url = reverse('plans:plans_index')
    response = client.get(url)

    # redirection to login page
    assert 302 == response.status_code


@pytest.mark.django_db()
def test_view_index_func(client):
    view = resolve('/plans/')

    assert Index == view.func.view_class


# ----------------------------------------------------------------------------
#                                                                  plans_stats
# ----------------------------------------------------------------------------
@pytest.mark.django_db()
def test_view_plan_stats_render(client, login):
    url = reverse('plans:reload_plan_stats')

    response = client.get(url, {'ajax_trigger': True})

    assert 200 == response.status_code


@pytest.mark.django_db()
def test_view_plan_stats_render_to_string(client, login):
    url = reverse('plans:reload_plan_stats')

    response = client.get(url, {'ajax_trigger': False})

    assert 200 == response.status_code


# ----------------------------------------------------------------------------
#                                                     IncomePlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_incomes(admin_client):
    url = reverse('plans:incomes_plan_new')
    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_incomes_new(client, login):
    i = IncomeTypeFactory()
    data = {'year': '1999', 'income_type': i.pk, 'january': 999.99}

    url = reverse('plans:incomes_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_incomes_new_invalid_data(client, login):
    data = {'year': 'x', 'income_type': 0, 'january': 999.99}

    url = reverse('plans:incomes_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_incomes_update(client, login):
    p = IncomePlanFactory(year=1999)

    data = {'year': '1999', 'income_type': p.income_type.pk, 'january': 999.99}
    url = reverse('plans:incomes_plan_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_incomes_update_year_not_match(client, login):
    # if year in Plan and urser.profile not match, 404 error
    p = IncomePlanFactory()

    url = reverse('plans:incomes_plan_update', kwargs={'pk': p.pk})

    response = client.get(url, {}, **X_Req)

    assert 404 == response.status_code


# ----------------------------------------------------------------------------
#                                                   ExpensesPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_expenses(admin_client):
    url = reverse('plans:expenses_plan_new')
    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_expenses_new(client, login):
    i = ExpenseTypeFactory()
    data = {'year': '1999', 'expense_type': i.pk, 'january': 999.99}

    url = reverse('plans:expenses_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_expenses_new_invalid_data(client, login):
    data = {'year': 'x', 'expense_type': 0, 'january': 999.99}

    url = reverse('plans:expenses_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_expenses_update(client, login):
    p = ExpensePlanFactory(year=1999)

    data = {'year': '1999', 'expense_type': p.expense_type.pk, 'january': 999.99}
    url = reverse('plans:expenses_plan_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_expenses_update_year_not_match(client, login):
    # if year in Plan and urser.profile not match, 404 error
    p = ExpensePlanFactory()

    url = reverse('plans:expenses_plan_update', kwargs={'pk': p.pk})

    response = client.get(url, {}, **X_Req)

    assert 404 == response.status_code


# ----------------------------------------------------------------------------
#                                                     SavingPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_savings(admin_client):
    url = reverse('plans:savings_plan_new')
    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_savings_new(client, login):
    i = SavingTypeFactory()
    data = {'year': '1999', 'saving_type': i.pk, 'january': 999.99}

    url = reverse('plans:savings_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_savings_new_invalid_data(client, login):
    data = {'year': 'x', 'saving_type': 0, 'january': 999.99}

    url = reverse('plans:savings_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_savings_update(client, login):
    p = SavingPlanFactory(year=1999)

    data = {'year': '1999', 'saving_type': p.saving_type.pk, 'january': 999.99}
    url = reverse('plans:savings_plan_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_savings_update_year_not_match(client, login):
    # if year in Plan and urser.profile not match, 404 error
    p = SavingPlanFactory()

    url = reverse('plans:savings_plan_update', kwargs={'pk': p.pk})

    response = client.get(url, {}, **X_Req)

    assert 404 == response.status_code


# ----------------------------------------------------------------------------
#                                                        DayPlan create/update
# ----------------------------------------------------------------------------
@freeze_time('1999-1-1')
def test_view_days(admin_client):
    url = reverse('plans:days_plan_new')
    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_days_new(client, login):
    data = {'year': '1999', 'january': 999.99}

    url = reverse('plans:days_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_days_new_invalid_data(client, login):
    data = {'year': 'x', 'january': 999.99}

    url = reverse('plans:days_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_days_update(client, login):
    p = DayPlanFactory(year=1999)

    data = {'year': '1999', 'january': 999.99}
    url = reverse('plans:days_plan_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_days_update_year_not_match(client, login):
    # if year in Plan and urser.profile not match, 404 error
    p = DayPlanFactory()

    url = reverse('plans:days_plan_update', kwargs={'pk': p.pk})

    response = client.get(url, {}, **X_Req)

    assert 404 == response.status_code


#
#         NecessaryPlan create/update
#
@freeze_time('1999-1-1')
def test_view_necessarys(admin_client):
    url = reverse('plans:necessarys_plan_new')
    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_necessarys_new(client, login):
    data = {'year': '1999', 'title': 'X', 'january': 999.99}

    url = reverse('plans:necessarys_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_necessarys_new_invalid_data(client, login):
    data = {'year': 'x', 'title': '', 'january': 999.99}

    url = reverse('plans:necessarys_plan_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_necessarys_update(client, login):
    p = NecessaryPlanFactory(year=1999)

    data = {'year': '1999',  'title': 'X', 'january': 999.99}
    url = reverse('plans:necessarys_plan_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999,99' in actual['html_list']


@pytest.mark.django_db()
def test_view_necessarys_update_year_not_match(client, login):
    # if year in Plan and urser.profile not match, 404 error
    p = NecessaryPlanFactory()

    url = reverse('plans:necessarys_plan_update', kwargs={'pk': p.pk})

    response = client.get(url, {}, **X_Req)

    assert 404 == response.status_code
