import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from .. import views


@pytest.mark.django_db()
def test_set_year(client_logged):
    url = reverse(
        'core:set_year',
        kwargs={'year': 1970}
    )

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.year == 1970


@pytest.mark.django_db()
def test_set_month(client_logged):
    url = reverse(
        'core:set_month',
        kwargs={'month': 12}
    )

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.month == 12


def test_view_regenerate_balances():
    view = resolve('/set/balances/')

    assert views.regenerate_balances == view.func


def test_view_regenerate_balances_current_year():
    view = resolve('/set/balances/1999/')

    assert views.regenerate_balances_current_year == view.func


@pytest.mark.django_db
def test_view_regenerate_balances_status_200(client_logged):
    url = reverse('core:regenerate_balances')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_regenerate_balances_current_year_status_200(client_logged):
    url = reverse(
        'core:regenerate_balances_current_year',
        kwargs={'year': 1999}
    )
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200


@freeze_time('2007-01-01')
@patch('project.core.views.post_save_saving_stats')
@patch('project.core.views.post_save_account_stats')
@patch('project.core.views.post_save_pension_stats')
def test_view_regenerate_balances_func_called(mck_pension,
                                              mck_account,
                                              mck_saving,
                                              fake_request):
    views.regenerate_balances(fake_request)

    assert mck_account.call_count == 2
    assert mck_saving.call_count == 2
    assert mck_pension.call_count == 2


@patch('project.core.views.post_save_saving_stats')
@patch('project.core.views.post_save_account_stats')
@patch('project.core.views.post_save_pension_stats')
def test_view_regenerate_balances_current_year_func_called(mck_pension,
                                                           mck_account,
                                                           mck_saving,
                                                           fake_request):
    views.regenerate_balances_current_year(fake_request, 1999)

    assert mck_account.call_count == 1
    assert mck_saving.call_count == 1
    assert mck_pension.call_count == 1
