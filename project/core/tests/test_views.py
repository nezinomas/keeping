import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from ...accounts.factories import AccountFactory
from ...core.factories import ProfileFactory, UserFactory
from .. import views


@pytest.mark.django_db()
def test_set_year(login, client):
    url = reverse(
        'core:set_year',
        kwargs={'year': 1970, 'view_name': 'core:core_index'}
    )

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.year == 1970


@pytest.mark.django_db()
def test_set_month(login, client):
    url = reverse(
        'core:set_month',
        kwargs={'month': 12, 'view_name': 'core:core_index'}
    )

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.month == 12


def test_view_regenerate_balances():
    view = resolve('/set/balances/')

    assert views.regenerate_balances == view.func


def test_view_regenerate_balances_current_year():
    view = resolve('/set/balances/1999/')

    assert views.regenerate_balances_current_year == view.func


@pytest.mark.django_db
def test_view_regenerate_balances_status_200(login, client):
    url = reverse('core:regenerate_balances')
    response = client.get(url, follow=True)

    assert 200 == response.status_code


@pytest.mark.django_db
def test_view_regenerate_balances_current_year_status_200(login, client):
    url = reverse('core:regenerate_balances_current_year', kwargs={'year': 1999})
    response = client.get(url, follow=True)

    assert 200 == response.status_code


@freeze_time('2007-01-01')
@patch('project.core.views._account_update_or_create')
def test_view_regenerate_balances_func_called(mck, _fake_request):
    view = views.regenerate_balances(_fake_request)

    assert 4 == mck.call_count


@patch('project.core.views._account_update_or_create')
def test_view_regenerate_balances_current_year_func_called(mck, _fake_request):
    view = views.regenerate_balances_current_year(_fake_request, 1999)

    assert 1 == mck.call_count
