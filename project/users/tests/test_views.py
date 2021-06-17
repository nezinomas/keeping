import pytest
from django.contrib.auth import views as auth_views
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ...users.factories import UserFactory
from ..views import CustomLogin

pytestmark = pytest.mark.django_db


def test_custom_login_func():
    view = resolve('/login/')

    assert CustomLogin == view.func.view_class


def test_custom_logout_func():
    view = resolve('/logout/')

    assert auth_views.LogoutView == view.func.view_class


def test_successful_login(client):
    UserFactory()

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated


def test_journal_in_session(client):
    j = JournalFactory()

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    client.post(url, credentials, follow=True)

    actual = client.session.get('journal')

    assert actual.pk == j.pk


@freeze_time('2000-12-01')
@pytest.mark.disable_get_user_patch
def test_user_year_month_values_fill_on_login_if_empty(client):
    UserFactory(year=None, month=None)

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated

    assert response.context['user'].year == 2000
    assert response.context['user'].month == 12
