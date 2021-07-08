import pytest
from django.urls import resolve, reverse

from .. import views

pytestmark = pytest.mark.django_db


def test_settings_user_must_logged(client):
    url = reverse('users:settings_index')

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'login'


def test_settings_link_if_user_is_superuser(client_logged):
    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:settings_index')

    assert link in content


def test_settings_no_link_ordinary_user(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:settings_index')

    assert link not in content


def test_index_func():
    view = resolve('/settings/')

    assert views.SettingsIndex == view.func.view_class


def test_index_user_must_be_superuser(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('users:settings_index')

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'index'


def test_index_status_code(client_logged):
    url = reverse('users:settings_index')
    response = client_logged.get(url)

    assert response.status_code == 200
