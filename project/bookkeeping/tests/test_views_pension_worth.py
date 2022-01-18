import json

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...pensions.factories import PensionFactory, PensionTypeFactory
from .. import views

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


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

@freeze_time('1999-2-3')
def test_view_pension_worth_new(client_logged):
    PensionFactory()
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
