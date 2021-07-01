import re
from datetime import timedelta

import pytest
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.signing import TimestampSigner
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from freezegun import freeze_time

from ...config.secrets import get_secret
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
    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context['user'].is_authenticated


def test_user_journal(client):
    url = reverse('users:login')
    credentials = {'username': 'bob', 'password': '123'}

    response = client.post(url, credentials, follow=True)

    assert response.context['user'].journal.title == 'bob Journal'


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


def test_user_reset_link_if_form_has_errors(client):
    url = reverse('users:login')
    credentials = {'username': 'xxx', 'password': 'xxx'}

    response = client.post(url, credentials)

    assert response.status_code == 200

    content = response.content.decode('utf-8')
    reset = reverse('users:password_reset')

    assert f'href="{reset}"' in content


def test_user_no_reset_link(client):
    url = reverse('users:login')
    response = client.get(url)
    content = response.content.decode('utf-8')
    reset = reverse('users:password_reset')

    assert f'href="{reset}"' not in content


def test_user_signup_link(client):
    url = reverse('users:login')
    response = client.get(url)
    content = response.content.decode('utf-8')
    signup = reverse('users:signup')

    assert f'href="{signup}"' in content


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


def test_signup_no_link(client):
    url = reverse('users:signup')
    response = client.get(url)
    content = response.content.decode('utf-8')
    signup = reverse('users:signup')

    assert f'href="{signup}"' not in content

def test_signup_login_link(client):
    url = reverse('users:signup')
    response = client.get(url)
    content = response.content.decode('utf-8')
    login = reverse('users:login')

    assert f'href="{login}"' in content


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
        'password2': 'abcdef123456',
    }

    return client.post(url, data)


@pytest.mark.disable_get_user_patch
def test_signup_redirection(_signuped_client):
    assert _signuped_client.status_code == 302


@pytest.mark.disable_get_user_patch
def test_signup_user_creation(_signuped_client):
    users = User.objects.all()
    assert users.count() == 1

    user = users.first()

    assert user.is_superuser


@pytest.mark.disable_get_user_patch
def test_signup_user_authentication(client, _signuped_client):
    url = reverse('bookkeeping:index')
    response = client.get(url)
    user = response.context.get('user')

    assert user.is_authenticated


@pytest.mark.disable_get_user_patch
def test_signup_journal_creation(_signuped_client):
    journals = Journal.objects.all()
    assert journals.count() == 1

    journal = journals[0]

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


# ---------------------------------------------------------------------------------------
#                                                                         Password Change
# --------------------------------------------------------------------------------------
def test_password_change_func():
    view = resolve('/password_change/')
    assert view.func.view_class is views.PasswordChange


def test_password_change_status_code(client_logged):
    url = reverse('users:password_change')
    response = client_logged.get(url)
    assert response.status_code == 200


def test_password_change_form(client_logged):
    url = reverse('users:password_change')
    response = client_logged.get(url)

    form = response.context.get('form')

    assert isinstance(form, PasswordChangeForm)


def test_password_change_form_inputs(client_logged):
    url = reverse('users:password_change')
    response = client_logged.get(url)

    form = response.content.decode('utf-8')

    assert form.count('<input') == 5
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="password"') == 3


def test_password_change_redirect_to_login(client):
    url = reverse('users:password_change')
    response = client.get(url, follow=True)

    assert response.resolver_match.url_name == 'login'


@pytest.fixture
def _change_valid_data():
    return {
        'old_password': '123',
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    }


def test_password_change_succesful_redirect(client_logged, _change_valid_data):
    url = reverse('users:password_change')
    response = client_logged.post(url, _change_valid_data, follow=True)

    assert response.resolver_match.url_name == 'password_change_done'


def test_password_change_changed(client_logged, _change_valid_data):
    url = reverse('users:password_change')
    client_logged.post(url, _change_valid_data, follow=True)

    user = User.objects.first()

    assert user.check_password('new_password')


def test_password_change_authentication(client_logged, _change_valid_data):
    url = reverse('users:password_change')
    client_logged.post(url, _change_valid_data, follow=True)

    '''
    Create a new request to an arbitrary page.
    The resulting response should now have an `user` to its context,
    after a successful sign up.
    '''

    response = client_logged.get(reverse('bookkeeping:index'))
    user = response.context.get('user')
    assert user.is_authenticated


def test_password_change_invalid_status_code(client_logged):
    url = reverse('users:password_change')
    response = client_logged.post(url, {})
    assert response.status_code == 200


def test_password_change_invalid_form_error(client_logged):
    url = reverse('users:password_change')
    response = client_logged.post(url, {})
    form = response.context.get('form')

    assert form.errors


def test_password_change_invalid_didnt_change_password(client_logged):
    url = reverse('users:password_change')
    client_logged.post(url, {})

    user = User.objects.first()

    assert user.check_password('123')


# ---------------------------------------------------------------------------------------
#                                                                                  Invite
# ---------------------------------------------------------------------------------------
def test_invite_func():
    view = resolve('/invite/')
    assert view.func.view_class is views.Invite


def test_invite_user_must_be_superuser(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('users:invite')

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'index'


def test_invite_link_is_superuser(client_logged):
    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:invite')

    assert link in content


def test_invite_no_link_ordinary_userr(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:invite')

    assert link not in content


def test_invite_status_code(client_logged):
    url = reverse('users:invite')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_invite_user_must_logged(client):
    url = reverse('users:invite')

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'login'


def test_invite_contains_form(client_logged):
    url = reverse('users:invite')
    response = client_logged.get(url)
    form = response.context.get('form')

    assert isinstance(form, forms.InviteForm)


def test_invite_form_inputs(client_logged):
    url = reverse('users:invite')
    response = client_logged.get(url)

    form = response.content.decode('utf-8')

    assert form.count('<input') == 2
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="email"') == 1


def test_invite_redirection(client_logged):
    '''
    A valid form submission should redirect the user to `invite_done` view
    '''
    user = UserFactory()
    url = reverse('users:invite')
    response = client_logged.post(url, {'email': user.email}, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'invite_done'


def test_invite_email_subject(client_logged):
    user = UserFactory()
    url = reverse('users:invite')
    client_logged.post(url, {'email': user.email})
    email = mail.outbox[0].subject

    assert email == f'{user.username} invitation'


def test_invite_crypted_link(client_logged):
    user = UserFactory()
    url = reverse('users:invite')
    client_logged.post(url, {'email': user.email})
    email = mail.outbox[0].body

    token = re.findall(r'http://.*?\/([\w\-]{23,}:[\w\-]{6}:[\w\-]{43})', email)[0]
    signer = TimestampSigner(salt=get_secret('SALT'))
    actual = signer.unsign_object(token, max_age=timedelta(days=3))
    expect = {'jrn': user.journal.pk, 'usr': user.pk}

    assert expect == actual


def test_invite_body(client_logged):
    user = UserFactory()
    url = reverse('users:invite')
    client_logged.post(url, {'email': user.email})
    email = mail.outbox[0].body

    assert user.username in email
    assert reverse('users:invite') in email


# ---------------------------------------------------------------------------------------
#                                                                         Invite Complete
# ---------------------------------------------------------------------------------------
def test_invite_complete_func():
    view = resolve('/invite/done/')
    assert view.func.view_class is views.InviteDone


def test_invite_complete_status_code(client):
    url = reverse('users:invite_done')
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'login'
