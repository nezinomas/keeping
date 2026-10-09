import re
from datetime import timedelta

import pytest
import time_machine
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ....journals.models import Journal
from ....users.models import User
from ....users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_successful_login(client):
    url = reverse("users:login")
    credentials = {"username": "bob", "password": "123"}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context["user"].is_authenticated


def test_user_journal(client):
    url = reverse("users:login")
    credentials = {"username": "bob", "password": "123"}

    response = client.post(url, credentials, follow=True)

    assert response.context["user"].journal.title == "bob Journal"


@pytest.mark.disable_get_user_patch
@time_machine.travel("2000-12-15")
def test_user_year_month_values_fill_on_login_if_empty(client):
    UserFactory(year=None, month=None)

    url = reverse("users:login")
    credentials = {"username": "bob", "password": "123"}

    response = client.post(url, credentials, follow=True)

    assert response.status_code == 200
    assert response.context["user"].is_authenticated

    assert response.context["user"].year == 2000
    assert response.context["user"].month == 12


def test_user_reset_link_if_form_has_errors(client):
    url = reverse("users:login")
    credentials = {"username": "xxx", "password": "xxx"}

    response = client.post(url, credentials)

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    reset = reverse("users:password_reset")

    assert f'href="{reset}"' in content


def test_user_no_reset_link(client):
    url = reverse("users:login")
    response = client.get(url)
    content = response.content.decode("utf-8")
    reset = reverse("users:password_reset")

    assert f'href="{reset}"' not in content


@override_settings(ENV={"CAN_SIGN_UP": True})
def test_user_signup_link(client):
    url = reverse("users:login")
    response = client.get(url)
    content = response.content.decode("utf-8")
    signup = reverse("users:signup")

    assert f'href="{signup}"' in content


def test_logout_user_is_logged(client_logged):
    url = reverse("users:logout")

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "login"


@pytest.mark.parametrize(
    "url_name",
    ["users:logout", "users:password_change", "users:invite", "users:settings_index"],
    ids=["logout", "password_change", "invite", "settings_index"],
)
def test_anonymous_user_is_sent_to_login(client, url_name):
    response = client.get(reverse(url_name), follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "login"


@pytest.mark.parametrize(
    "url_name", ["users:invite", "users:settings_index"], ids=["invite", "index"]
)
def test_ordinary_user_is_sent_to_index(main_user, client_logged, url_name):
    main_user.is_superuser = False
    main_user.save()

    response = client_logged.get(reverse(url_name), follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "index"


@override_settings(ENV={"CAN_SIGN_UP": False})
def test_signup_redirects_to_login(client):
    url = reverse("users:signup")
    response = client.get(url, follow=True)

    assert response.resolver_match.view_name == "users:login"


@override_settings(ENV={"CAN_SIGN_UP": True})
def test_signup_no_link(client):
    url = reverse("users:signup")
    response = client.get(url)
    content = response.content.decode("utf-8")
    signup = reverse("users:signup")

    assert f'href="{signup}"' not in content


@override_settings(ENV={"CAN_SIGN_UP": True})
def test_signup_login_link(client):
    url = reverse("users:signup")
    response = client.get(url)
    content = response.content.decode("utf-8")
    login = reverse("users:login")

    assert f'href="{login}"' in content


@override_settings(ENV={"CAN_SIGN_UP": True})
def test_signup_form_inputs(client):
    url = reverse("users:signup")
    response = client.get(url)

    form = response.content.decode("utf-8")

    assert form.count("<input") == 6
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="hidden" name="next"') == 1
    assert form.count('type="text"') == 1
    assert form.count('type="email"') == 1
    assert form.count('type="password"') == 2


@pytest.fixture
@override_settings(ENV={"CAN_SIGN_UP": True})
def _signuped_client(client):
    url = reverse("users:signup")
    data = {
        "username": "john",
        "email": "john@dot.com",
        "password1": "abcdef123456",
        "password2": "abcdef123456",
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
    url = reverse("bookkeeping:index")
    response = client.get(url)
    user = response.context.get("user")

    assert user.is_authenticated


@pytest.mark.disable_get_user_patch
def test_signup_journal_creation(_signuped_client):
    journals = Journal.objects.all()
    assert journals.count() == 1

    journal = journals[0]

    assert str(journal) == "john Journal"


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.disable_get_user_patch
def test_signup_form_errors(client):
    url = reverse("users:signup")
    response = client.post(url, {})
    form = response.context.get("form")

    assert form.errors


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.disable_get_user_patch
def test_signup_dont_create_user(client):
    url = reverse("users:signup")
    client.post(url, {})

    assert not User.objects.exists()


def test_password_reset_form_inputs(client):
    url = reverse("users:password_reset")
    response = client.get(url)

    form = response.content.decode("utf-8")

    assert form.count("<input") == 3
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="hidden" name="next"') == 1
    assert form.count('type="email"') == 1


@pytest.mark.parametrize(
    "email_of",
    [lambda user: user.email, lambda user: "xxx@xxx.yy"],
    ids=["known_email", "unknown_email"],
)
def test_password_reset_redirection(client, email_of):
    user = UserFactory()
    url = reverse("users:password_reset")
    response = client.post(url, {"email": email_of(user)}, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "password_reset_done"


def test_password_reset_no_email_send(client):
    UserFactory()
    url = reverse("users:password_reset")
    client.post(url, {"email": "xxx@xxx.yy"}, follow=True)

    assert len(mail.outbox) == 0


def test_password_reset_email_subject(client):
    user = UserFactory()
    url = reverse("users:password_reset")
    client.post(url, {"email": user.email})
    email = mail.outbox[0].subject

    assert email == "Please reset your password"


def test_password_reset_email_body(client):
    user = UserFactory()
    url = reverse("users:password_reset")
    response = client.post(url, {"email": user.email})
    context = response.context
    token = context.get("token")
    uid = context.get("uid")
    password_reset_token_url = reverse(
        "users:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
    )
    email = mail.outbox[0].body

    assert password_reset_token_url in email
    assert user.username in email
    assert user.email in email


@pytest.mark.parametrize(
    "url_name",
    ["users:password_reset_done", "users:password_reset_complete"],
    ids=["reset_done", "reset_complete"],
)
def test_reset_pages_link_back_to_login(client, url_name):
    response = client.get(reverse(url_name))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'href="{reverse("users:login")}"' in content


@pytest.fixture
def _valid_confirm_response(client):
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    url = reverse(
        "users:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
    )

    return client.get(url, follow=True)


def test_password_reset_confirm_form_inputs(_valid_confirm_response):
    response = _valid_confirm_response

    form = response.content.decode("utf-8")

    assert form.count("<input") == 4
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count('type="password"') == 2


@pytest.fixture
def _invalid_confirm_response(client):
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # invalidate the token by changing the password
    user.set_password("xxx")
    user.save()

    url = reverse(
        "users:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
    )
    return client.get(url, follow=True)


def test_password_reset_confirm_invalid_html(_invalid_confirm_response):
    response = _invalid_confirm_response
    url = reverse("users:password_reset")
    content = response.content.decode("utf-8")

    assert f'href="{url}"' in content
    assert "Prašyti naujos slaptažodžio atstatymo nuorodos" in content


@pytest.mark.parametrize(
    "url_name, inputs, field, fields",
    [
        ("users:password_change", 5, 'type="password"', 3),
        ("users:invite", 2, 'type="email"', 1),
    ],
    ids=["password_change", "invite"],
)
def test_form_inputs(client_logged, url_name, inputs, field, fields):
    response = client_logged.get(reverse(url_name))
    form = response.content.decode("utf-8")

    assert form.count("<input") == inputs
    assert form.count('type="hidden" name="csrfmiddlewaretoken"') == 1
    assert form.count(field) == fields


@pytest.fixture
def _change_valid_data():
    return {
        "old_password": "123",
        "new_password1": "new_password",
        "new_password2": "new_password",
    }


def test_password_change_successful_redirect(client_logged, _change_valid_data):
    url = reverse("users:password_change")
    response = client_logged.post(url, _change_valid_data, follow=True)

    assert response.resolver_match.url_name == "password_change_done"


def test_password_change_changed(client_logged, _change_valid_data):
    url = reverse("users:password_change")
    client_logged.post(url, _change_valid_data, follow=True)

    user = User.objects.first()

    assert user.check_password("new_password")


def test_password_change_authentication(client_logged, _change_valid_data):
    url = reverse("users:password_change")
    client_logged.post(url, _change_valid_data, follow=True)

    response = client_logged.get(reverse("bookkeeping:index"))
    user = response.context.get("user")

    assert user.is_authenticated


def test_password_change_invalid_form_error(client_logged):
    url = reverse("users:password_change")
    response = client_logged.post(url, {})
    form = response.context.get("form")

    assert form.errors


def test_password_change_invalid_didnt_change_password(client_logged):
    url = reverse("users:password_change")
    client_logged.post(url, {})

    user = User.objects.first()

    assert user.check_password("123")


@pytest.mark.parametrize("is_superuser", [True, False], ids=["super", "ordinary"])
def test_invite_link_on_settings_page(main_user, client_logged, is_superuser):
    main_user.is_superuser = is_superuser
    main_user.save()

    response = client_logged.get(reverse("users:settings_index"), follow=True)
    content = response.content.decode("utf-8")

    assert (reverse("users:invite") in content) is is_superuser


@pytest.mark.parametrize("is_superuser", [True, False], ids=["super", "ordinary"])
def test_settings_link_in_the_nav(main_user, client_logged, is_superuser):
    main_user.is_superuser = is_superuser
    main_user.save()

    response = client_logged.get(reverse("bookkeeping:index"))
    content = response.content.decode("utf-8")

    assert (reverse("users:settings_index") in content) is is_superuser


def test_invite_email_subject(client_logged, main_user):
    url = reverse("users:invite")
    client_logged.post(url, {"email": "john@test.com"})

    email = mail.outbox[0].subject

    assert email == f"{main_user.username} invitation"


def test_invite_crypted_link(client_logged, main_user):
    url = reverse("users:invite")
    client_logged.post(url, {"email": "john@test.com"})
    email = mail.outbox[0].body

    token = re.findall(r"http://.*?\/([\w\-]{23,}:[\w\-]{6}:[\w\-]{43})", email)[0]
    signer = TimestampSigner(salt=settings.SALT)
    actual = signer.unsign_object(token, max_age=timedelta(days=3))
    expect = {"jrn": main_user.journal.pk, "usr": main_user.pk}

    assert expect == actual


def test_invite_body(client_logged, main_user):
    url = reverse("users:invite")
    client_logged.post(url, {"email": "john@test.com"})
    email = mail.outbox[0].body

    assert main_user.username in email
    assert reverse("users:invite") in email


def test_invite_done_says_the_email_was_sent(client_logged):
    url = reverse("users:invite_done")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "Laiškas išsiųstas" in content
    assert 'id="submit"' not in content


@pytest.fixture()
def signer(main_user):
    signer_ = TimestampSigner(salt=settings.SALT)
    token_ = signer_.sign_object({"jrn": main_user.journal.pk, "usr": main_user.pk})
    return (signer_, token_)


def test_invite_signup_expired_link(client, main_user):
    with time_machine.travel("1974-1-1 1:0:0"):
        s_ = TimestampSigner(salt=settings.SALT)
        token_ = s_.sign_object({"jrn": main_user.journal.pk, "usr": main_user.pk})

    with time_machine.travel("1974-1-4 1:0:1"):
        url = reverse("users:invite_signup", kwargs={"token": token_})
        response = client.get(url)
        content = response.content.decode("utf-8")

        assert 'type="hidden" name="csrfmiddlewaretoken"' not in content
        assert (
            "Atrodo, kad jūsų kvietimas nebegalioja. Paprašykite draugo atsiųsti naują nuorodą."  # noqa: E501
            in content
        )


def test_invite_signup_valid_link(client, signer):
    _, token_ = signer

    url = reverse("users:invite_signup", kwargs={"token": token_})
    response = client.get(url)
    content = response.content.decode("utf-8")

    assert 'type="hidden" name="csrfmiddlewaretoken"' in content
    assert (
        "Atrodo, kad jūsų kvietimas nebegalioja. Paprašykite draugo atsiųsti naują nuorodą."  # noqa: E501
        not in content
    )


def test_invite_signup_edited_token(client):
    url = reverse(
        "users:invite_signup",
        kwargs={"token": "x" * 23 + ":" + "x" * 5 + ":" + "x" * 43},
    )
    response = client.get(url)
    content = response.content.decode("utf-8")

    assert (
        "Atrodo, kad jūsų kvietimas nebegalioja. Paprašykite draugo atsiųsti naują nuorodą."  # noqa: E501
        in content
    )


@pytest.fixture
def _invite_client(main_user, client):
    signer_ = TimestampSigner(salt=settings.SALT)
    token_ = signer_.sign_object({"jrn": main_user.journal.pk, "usr": main_user.pk})
    url = reverse("users:invite_signup", kwargs={"token": token_})

    data = {
        "username": "john",
        "email": "john@dot.com",
        "password1": "abcdef123456",
        "password2": "abcdef123456",
    }

    return client.post(url, data)


def test_invite_signup_redirection(_invite_client):
    assert _invite_client.status_code == 302


@pytest.mark.parametrize(
    "error", [AttributeError, ObjectDoesNotExist], ids=["broken_user", "no_object"]
)
def test_invite_signup_broken_user(mocker, client, main_user, error):
    mck = mocker.patch("project.users.views.User")
    mck.objects.get.side_effect = error

    signer_ = TimestampSigner(salt=settings.SALT)
    token_ = signer_.sign_object({"jrn": main_user.journal.pk, "usr": main_user.pk})
    url = reverse("users:invite_signup", kwargs={"token": token_})

    data = {
        "username": "john",
        "email": "john@dot.com",
        "password1": "abcdef123456",
        "password2": "abcdef123456",
    }

    client.post(url, data)

    assert User.objects.all().count() == 1


def test_invite_signup_user_creation(_invite_client):
    users = User.objects.all()
    assert users.count() == 2

    user = users.last()

    assert not user.is_superuser
    assert user.username == "john"
    assert user.journal.title == "bob Journal"


def test_invite_signup_journals(_invite_client):
    journals = Journal.objects.all()
    assert journals.count() == 1

    journal = journals[0]

    assert str(journal) == "bob Journal"


def test_user_delete_other_user_get_form(client_logged, second_user):
    url = reverse("users:settings_users_delete", kwargs={"pk": second_user.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_user_delete_other_user_post_form(client_logged, second_user):
    url = reverse("users:settings_users_delete", kwargs={"pk": second_user.pk})
    client_logged.post(url)

    assert User.objects.all().count() == 2
