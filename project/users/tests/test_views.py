import pytest
from django.contrib.auth import views as auth_views
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...users.factories import UserFactory
from ..views import CustomLogin


def test_custom_login_func():
    view = resolve('/login/')

    assert CustomLogin == view.func.view_class


def test_custom_logout_func():
    view = resolve('/logout/')

    assert auth_views.LogoutView == view.func.view_class


@pytest.mark.django_db
def test_successful_login(client):
    UserFactory()

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated


@pytest.mark.django_db
@freeze_time('2000-01-01')
def test_fill_user_on_login(client):
    UserFactory(year=None, month=None)

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated

    assert response.context['user'].year == 2000
    assert response.context['user'].month == 1
