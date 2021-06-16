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


def test_journal_id_in_session(client):
    j = JournalFactory()

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    client.post(url, credentials, follow=True)

    assert client.session.get('journal') == j.pk
    assert client.session.get('year') == j.year
    assert client.session.get('month') == j.month


@freeze_time('2000-12-01')
def test_journal_year_month_values_fill_on_login_if_empty(client):
    j = JournalFactory()
    j.year = None
    j.month = None
    j.save()

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    client.post(url, credentials, follow=True)

    actual = Journal.objects.related().first()

    assert actual.year == 2000
    assert actual.month == 12
