import json

import pytest
from django.urls import resolve, reverse

from ...core.tests.utils import setup_view
from ...savings.factories import SavingTypeFactory
from .. import views


pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


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
    assert actual.get('html_list')


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
