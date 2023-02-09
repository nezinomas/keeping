import pytest
from django.urls import resolve, reverse

from ...pensions.factories import PensionFactory, PensionTypeFactory
from .. import views
from ..models import PensionWorth

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                           Pension Worth
# ---------------------------------------------------------------------------------------
def test_view_func():
    view = resolve('/bookkeeping/pensions_worth/new/')

    assert views.PensionsWorthNew == view.func.view_class


def test_view_200(client_logged):
    response = client_logged.get('/bookkeeping/pensions_worth/new/')

    assert response.status_code == 200


def test_formset_load(client_logged):
    PensionFactory()

    url = reverse('bookkeeping:pensions_worth_new')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert response.status_code == 200
    assert 'Pensijų vertė' in actual
    assert '<option value="1" selected>PensionType</option>' in actual


def test_formset_new(client_logged):
    i = PensionTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-date': '1999-2-3',
        'form-0-price': '999',
        'form-0-pension_type': i.pk
    }

    url = reverse('bookkeeping:pensions_worth_new')
    client_logged.post(url, data)

    actual = PensionWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 2
    assert actual.date.day == 3


def test_formset_valid_data(client_logged):
    i = PensionTypeFactory()
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-date': '1999-9-8',
        'form-0-price': '999',
        'form-0-pension_type': i.pk
    }

    url = reverse('bookkeeping:pensions_worth_new')
    client_logged.post(url, data)

    actual = PensionWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 9
    assert actual.date.day == 8


def test_formset_invalid_data(client_logged):
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-0-date': 'x',
        'form-0-price': 'x',
        'form-0-pension_type': 0
    }

    url = reverse('bookkeeping:pensions_worth_new')
    response = client_logged.post(url, data)
    form = response.context['formset']

    assert not form.is_valid()
    assert 'date' in form.errors[0]
    assert 'price' in form.errors[0]
    assert 'pension_type' in form.errors[0]
