import pytest
from django.urls import resolve, reverse

from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ...users.factories import User, UserFactory
from .. import views

pytestmark = pytest.mark.django_db

# ---------------------------------------------------------------------------------------
#                                                                                Settings
# ---------------------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------------------
#                                                                          Settings Index
# ---------------------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------------------
#                                                                          Settings Users
# ---------------------------------------------------------------------------------------
def test_users_func():
    view = resolve('/settings/users/')

    assert views.SettingsUsers == view.func.view_class


def test_users_status_code(client_logged):
    url = reverse('users:settings_users')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_users_no_additional_users(client_logged):
    url = reverse('users:settings_users')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'There are no additional users.' in actual


def test_users_one_additional_user(get_user, client_logged):
    UserFactory(username='X', is_superuser=False, journal=get_user.journal)
    UserFactory(username='Y', journal=JournalFactory(title='YY'))

    url = reverse('users:settings_users')
    response = client_logged.get(url)
    actual = response.context['items']

    assert Journal.objects.all().count() == 2
    assert User.objects.all().count() == 3
    assert len(actual) == 1
