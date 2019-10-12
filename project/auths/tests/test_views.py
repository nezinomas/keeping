import pytest
from django.contrib.auth import views as auth_views
from django.urls import resolve, reverse
from ...core.factories import UserFactory, ProfileFactory
from ..views import CustomLogin
from freezegun import freeze_time

def test_custom_login_func():
    view = resolve('/login/')

    assert CustomLogin == view.func.view_class


def test_custom_logout_func():
    view = resolve('/logout/')

    assert auth_views.LogoutView == view.func.view_class


@pytest.mark.django_db
def test_successful_login(client):
    UserFactory()

    url = reverse('auths:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert 200 == response.status_code
    assert response.context['user'].is_authenticated


@pytest.mark.django_db
@freeze_time('2000-01-01')
def test_fill_user_profile_on_login(client):
    p = ProfileFactory(year=None, month=None)

    url = reverse('auths:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert 200 == response.status_code
    assert response.context['user'].is_authenticated

    assert 2000 == response.context['user'].profile.year
    assert 1 == response.context['user'].profile.month
