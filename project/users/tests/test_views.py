import pytest
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
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

    assert views.Logout is view.func.view_class


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
    client.post(url, {})

    assert not User.objects.exists()


# ---------------------------------------------------------------------------------------
#                                                                          Password Reset
# ---------------------------------------------------------------------------------------
def test_password_reset_func():
    view = resolve('/password_reset/')
    assert view.func.view_class is views.PasswordReset


def test_password_reset_status_code(client):
    url = reverse('users:password_reset')
    response = client.get(url)

    assert response.status_code == 200


def test_password_reset_contains_form(client):
    url = reverse('users:password_reset')
    response = client.get(url)
    form = response.context.get('form')

    assert isinstance(form, PasswordResetForm)


def test_password_reset_form_inputs(client):
    url = reverse('users:password_reset')
    response = client.get(url)

    form = response.content.decode('utf-8')

    assert form.count('<input') == 3
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="hidden" name="next"') == 1
    assert form.count('type="email"') == 1


def test_password_reset_redirection(client):
    '''
    A valid form submission should redirect the user to `password_reset_done` view
    '''
    user = UserFactory()
    url = reverse('users:password_reset')
    response = client.post(url, {'email': user.email}, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'password_reset_done'


def test_password_reset_redirection_invalid_email(client):
    '''
    Even invalid emails in the database should
    redirect the user to `password_reset_done` view
    '''
    UserFactory()
    url = reverse('users:password_reset')
    response = client.post(url, {'email': 'xxx@xxx.yy'}, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'password_reset_done'


def test_password_reset_no_email_send(client):
    UserFactory()
    url = reverse('users:password_reset')
    client.post(url, {'email': 'xxx@xxx.yy'}, follow=True)

    assert len(mail.outbox) == 0


def test_password_reset_email_subject(client):
    user = UserFactory()
    url = reverse('users:password_reset')
    client.post(url, {'email': user.email})
    email = mail.outbox[0].subject

    assert email == 'Please reset your password'


def test_password_reset_email_body(client):
    user = UserFactory()
    url = reverse('users:password_reset')
    response = client.post(url, {'email': user.email})
    context = response.context
    token = context.get('token')
    uid = context.get('uid')
    password_reset_token_url = reverse('users:password_reset_confirm', kwargs={
        'uidb64': uid,
        'token': token
    })
    email = mail.outbox[0].body

    assert password_reset_token_url in email
    assert user.username in email
    assert user.email in email


# ---------------------------------------------------------------------------------------
#                                                                    Password Reset Done
# ---------------------------------------------------------------------------------------
def test_password_reset_done_func():
    view = resolve('/password_reset/done/')
    assert view.func.view_class is views.PasswordResetDone


def test_password_reset_done_status_code(client):
    url = reverse('users:password_reset_done')
    response = client.get(url)

    assert response.status_code == 200


# ---------------------------------------------------------------------------------------
#                                                                  Password Reset Confirm
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _confirm_valid(client):
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    url = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

    response = client.get(url, follow=True)
    return (uid, token, response)


def test_password_reset_confirm_func(_confirm_valid):
    uid, token, _ = _confirm_valid

    view = resolve(f'/reset/{uid}/{token}/')
    assert view.func.view_class is views.PasswordResetConfirm


def test_password_reset_confirm_status_code(_confirm_valid):
    _, _, response = _confirm_valid

    assert response.status_code == 200


def test_password_reset_confirm_form(_confirm_valid):
    _, _, response = _confirm_valid

    form = response.context.get('form')

    assert isinstance(form, SetPasswordForm)


def test_password_reset_confirm_form_inputs(_confirm_valid):
    _, _, response = _confirm_valid

    form = response.content.decode('utf-8')

    assert form.count('<input') == 4
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="password"') == 2


@pytest.fixture
def _confirm_invalid(client):
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # invalidate the token by changing the password
    user.set_password('xxx')
    user.save()

    url = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    response = client.get(url, follow=True)
    return (uid, token, response)


def test_password_reset_confirm_invalid_status_code(_confirm_invalid):
    _, _, response = _confirm_invalid

    assert response.status_code == 200


def test_password_reset_confirm_incalid_html(_confirm_invalid):
    _, _, response = _confirm_invalid
    url = reverse('users:password_reset')
    content = response.content.decode('utf-8')

    assert f'href="{url}"' in content
    assert 'invalid password reset link' in content


# ---------------------------------------------------------------------------------------
#                                                                Password Reset Complete
# ---------------------------------------------------------------------------------------
def test_password_reset_complete_func():
    view = resolve('/reset/done/')
    assert view.func.view_class is views.PasswordResetComplete


def test_password_reset_complete_status_code(client):
    url = reverse('users:password_reset_complete')
    response = client.get(url)

    assert response.status_code == 200
