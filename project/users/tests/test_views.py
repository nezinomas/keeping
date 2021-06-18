import pytest
from django.contrib.auth import views as auth_views
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ...users.factories import UserFactory
from ...users.models import User
from .. import forms, views

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                  Log In
# ---------------------------------------------------------------------------------------
def test_custom_login_func():
    view = resolve('/login/')

    assert views.Login == view.func.view_class


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
@pytest.mark.disable_get_journal_patch
def test_user_year_month_values_fill_on_login_if_empty(client):
    UserFactory(year=None, month=None)

    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated

    assert response.context['user'].year == 2000
    assert response.context['user'].month == 12


# ---------------------------------------------------------------------------------------
#                                                                                 Log Out
# ---------------------------------------------------------------------------------------
def test_logout_func():
    view = resolve('/logout/')

    assert auth_views.LogoutView == view.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                                 Sign Up
# ---------------------------------------------------------------------------------------
def test_signup_func():
    view = resolve('/signup/')

    assert views.Signup == view.func.view_class


def test_signup_200(client):
    url = reverse('users:signup')
    response = client.get(url)

    assert response.status_code == 200


def test_signup_form(client):
    url = reverse('users:signup')
    response = client.get(url)

    form = response.context.get('form')

    assert isinstance(form, forms.SignUpForm)


def test_signup_form_inputs(client):
    url = reverse('users:signup')
    response = client.get(url)

    form = response.content.decode('utf-8')

    assert form.count('<input') == 6
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="hidden" name="next"') == 1
    assert form.count('type="text"') == 1
    assert form.count('type="email"') == 1
    assert form.count('type="password"') == 2


@pytest.fixture
def _signuped_client(client):
    url = reverse('users:signup')
    data = {
        'username': 'john',
        'email': 'john@dot.com',
        'password1': 'abcdef123456',
        'password2': 'abcdef123456'
    }

    return client.post(url, data)


@pytest.mark.disable_get_user_patch
@pytest.mark.disable_get_journal_patch
def test_signup_redirection(_signuped_client):
    assert _signuped_client.status_code == 302


@pytest.mark.disable_get_user_patch
@pytest.mark.disable_get_journal_patch
def test_signup_user_creation(_signuped_client):
    users = User.objects.all()
    assert users.count() == 1

    user = users.first()

    assert user.is_superuser


@pytest.mark.disable_get_user_patch
@pytest.mark.disable_get_journal_patch
def test_signup_user_authentication(client, _signuped_client):
    url = reverse('bookkeeping:index')
    response = client.get(url)
    user = response.context.get('user')

    assert user.is_authenticated


@pytest.mark.disable_get_user_patch
@pytest.mark.disable_get_journal_patch
def test_signup_journal_creation(_signuped_client):
    journals = Journal.objects.all()
    assert journals.count() == 1

    journal = journals.first()
    assert journal.user.username == 'john'
    assert str(journal) == 'john Journal'


@pytest.mark.disable_get_user_patch
def test_signup_invalid_status_code(client):
    url = reverse('users:signup')
    response = client.post(url, {})

    assert response.status_code == 200


@pytest.mark.disable_get_user_patch
def test_signup_form_errors(client):
    url = reverse('users:signup')
    response = client.post(url, {})
    form = response.context.get('form')

    assert form.errors


@pytest.mark.disable_get_user_patch
@pytest.mark.disable_get_journal_patch
def test_signup_dont_create_user(client):
    url = reverse('users:signup')
    response = client.post(url, {})

    assert not User.objects.exists()

