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


def test_view_regenerate_accounts():
    view = resolve('/set/accounts/')

    assert views.regenerate_accounts_balance == view.func


def test_view_regenerate_accounts_current_year():
    view = resolve('/set/accounts/1999/')

    assert views.regenerate_accounts_balance_current_year == view.func


def test_view_regenerate_accounts_status_200(admin_client):
    url = reverse('core:regenerate_accounts')
    response = admin_client.get(url, follow=True)

    assert 200 == response.status_code


def test_view_regenerate_accounts_current_year_status_200(admin_client):
    url = reverse('core:regenerate_accounts_current_year', kwargs={'year': 1999})
    response = admin_client.get(url, follow=True)

    assert 200 == response.status_code


@freeze_time('2007-01-01')
@patch('project.core.views._account_update_or_create')
def test_view_regenerate_accounts_func_called(mck, _fake_request):
    view = views.regenerate_accounts_balance(_fake_request)

    assert 4 == mck.call_count


@patch('project.core.views._account_update_or_create')
def test_view_regenerate_accounts_current_year_func_called(mck, _fake_request):
    view = views.regenerate_accounts_balance_current_year(_fake_request, 1999)

    assert 1 == mck.call_count


def test_view_regenerate_savings():
    view = resolve('/set/savings/')

    assert views.regenerate_savings_balance == view.func


def test_view_regenerate_savings_current_year():
    view = resolve('/set/savings/1999/')

    assert views.regenerate_savings_balance_current_year == view.func


def test_view_regenerate_savings_status_200(admin_client):
    url = reverse('core:regenerate_savings')
    response = admin_client.get(url, follow=True)

    assert 200 == response.status_code


def test_view_regenerate_savings_current_year_status_200(admin_client):
    url = reverse('core:regenerate_savings_current_year', kwargs={'year': 1999})
    response = admin_client.get(url, follow=True)

    assert 200 == response.status_code
