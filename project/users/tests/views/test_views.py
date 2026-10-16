import re
from datetime import timedelta

import pytest
import time_machine
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
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
    assert response.context["user"].journal.title == "bob Journal"


@pytest.mark.no_main_user
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


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize(
    "visit, link, present",
    [
        (
            lambda client: client.post(
                reverse("users:login"), {"username": "xxx", "password": "xxx"}
            ),
            "users:password_reset",
            True,
        ),
        (
            lambda client: client.get(reverse("users:login")),
            "users:password_reset",
            False,
        ),
        (lambda client: client.get(reverse("users:login")), "users:signup", True),
        (lambda client: client.get(reverse("users:signup")), "users:signup", False),
        (lambda client: client.get(reverse("users:signup")), "users:login", True),
    ],
    ids=[
        "login_errors_reset",
        "login_no_reset",
        "login_signup",
        "signup_no_signup",
        "signup_login",
    ],
)
def test_page_links(client, visit, link, present):
    response = visit(client)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert (f'href="{reverse(link)}"' in content) is present


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


REQUIRED = "Šis laukas yra privalomas."

SIGNUP = {
    "username": "john",
    "email": "john@dot.com",
    "password1": "abcdef123456",
    "password2": "abcdef123456",
}


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.no_main_user
def test_signup_user_authentication(client):
    client.post(reverse("users:signup"), SIGNUP)

    url = reverse("bookkeeping:index")
    response = client.get(url)
    user = response.context.get("user")

    assert user.is_authenticated


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.no_main_user
def test_signup_with_no_data_creates_no_user(client):
    response = client.post(reverse("users:signup"), {})

    assert REQUIRED in response.content.decode("utf-8")
    assert not User.objects.exists()


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


def _confirm_url():
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    return reverse(
        "users:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
    )


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


CSRF = 'type="hidden" name="csrfmiddlewaretoken"'
NEXT = 'type="hidden" name="next"'


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize(
    "url, counts",
    [
        (
            lambda: reverse("users:signup"),
            {
                "<input": 6,
                CSRF: 1,
                NEXT: 1,
                'type="text"': 1,
                'type="email"': 1,
                'type="password"': 2,
            },
        ),
        (
            lambda: reverse("users:password_reset"),
            {"<input": 3, CSRF: 1, NEXT: 1, 'type="email"': 1},
        ),
        (
            _confirm_url,
            {"<input": 4, CSRF: 1, 'type="password"': 2},
        ),
        (
            lambda: reverse("users:password_change"),
            {"<input": 5, CSRF: 1, 'type="password"': 3},
        ),
        (
            lambda: reverse("users:invite"),
            {"<input": 2, CSRF: 1, 'type="email"': 1},
        ),
    ],
    ids=[
        "signup",
        "password_reset",
        "password_reset_confirm",
        "password_change",
        "invite",
    ],
)
def test_form_inputs(client_logged, url, counts):
    form = client_logged.get(url(), follow=True).content.decode("utf-8")

    for markup, expected in counts.items():
        assert form.count(markup) == expected, markup


@pytest.fixture
def _change_valid_data():
    return {
        "old_password": "123",
        "new_password1": "new_password",
        "new_password2": "new_password",
    }


def test_password_change_changes_the_password_and_keeps_the_login(
    client_logged, main_user, _change_valid_data
):
    url = reverse("users:password_change")
    response = client_logged.post(url, _change_valid_data, follow=True)

    main_user.refresh_from_db()
    index = client_logged.get(reverse("bookkeeping:index"))

    assert response.resolver_match.url_name == "password_change_done"
    assert main_user.check_password("new_password")
    assert index.context.get("user").is_authenticated


def test_password_change_with_no_data_keeps_the_password(client_logged, main_user):
    url = reverse("users:password_change")
    response = client_logged.post(url, {})

    main_user.refresh_from_db()

    assert REQUIRED in response.content.decode("utf-8")
    assert main_user.check_password("123")


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


INVITE_EXPIRED = (
    "Atrodo, kad jūsų kvietimas nebegalioja. Paprašykite draugo atsiųsti naują nuorodą."
)


def _invite_url(user):
    token = TimestampSigner(salt=settings.SALT).sign_object(
        {"jrn": user.journal.pk, "usr": user.pk}
    )
    return reverse("users:invite_signup", kwargs={"token": token})


def test_invite_signup_expired_link(client, main_user):
    with time_machine.travel("1974-1-1 1:0:0"):
        url = _invite_url(main_user)

    with time_machine.travel("1974-1-4 1:0:1"):
        content = client.get(url).content.decode("utf-8")

    assert 'type="hidden" name="csrfmiddlewaretoken"' not in content
    assert INVITE_EXPIRED in content


def test_invite_signup_valid_link(client, main_user):
    content = client.get(_invite_url(main_user)).content.decode("utf-8")

    assert 'type="hidden" name="csrfmiddlewaretoken"' in content
    assert INVITE_EXPIRED not in content


def test_invite_signup_edited_token(client):
    url = reverse(
        "users:invite_signup",
        kwargs={"token": "x" * 23 + ":" + "x" * 5 + ":" + "x" * 43},
    )
    response = client.get(url)
    content = response.content.decode("utf-8")

    assert INVITE_EXPIRED in content


@pytest.mark.parametrize(
    "token",
    [
        lambda main_user, second_user: {
            "jrn": second_user.journal.pk,
            "usr": main_user.pk,
        },
        lambda main_user, second_user: {
            "jrn": main_user.journal.pk,
            "usr": main_user.pk + 100,
        },
    ],
    ids=["another_journal", "unknown_user"],
)
def test_invite_signup_of_a_missing_inviter_creates_no_user(
    client, main_user, second_user, token
):
    signed = TimestampSigner(salt=settings.SALT).sign_object(
        token(main_user, second_user)
    )
    url = reverse("users:invite_signup", kwargs={"token": signed})

    response = client.post(url, SIGNUP)

    assert response.url == reverse("users:login")
    assert not User.objects.filter(username="john").exists()


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize(
    ("url", "redirect", "is_superuser", "journal_title", "journals"),
    [
        (
            lambda user: reverse("users:signup"),
            "bookkeeping:index",
            True,
            "john Journal",
            2,
        ),
        (_invite_url, "users:login", False, "bob Journal", 1),
    ],
    ids=["signup", "invite_signup"],
)
def test_signup_creates_the_user(
    client, main_user, url, redirect, is_superuser, journal_title, journals
):
    response = client.post(url(main_user), SIGNUP)

    user = User.objects.get(username="john")

    assert response.url == reverse(redirect)
    assert User.objects.count() == 2
    assert user.is_superuser is is_superuser
    assert user.journal.title == journal_title
    assert Journal.objects.count() == journals


def test_user_delete_other_user_get_form(client_logged, second_user):
    url = reverse("users:settings_users_delete", kwargs={"pk": second_user.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_user_delete_other_user_post_form(client_logged, second_user):
    url = reverse("users:settings_users_delete", kwargs={"pk": second_user.pk})
    client_logged.post(url)

    assert User.objects.all().count() == 2


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize(
    ("url", "journal_title"),
    [
        (lambda user: reverse("users:signup"), "john Journal"),
        (_invite_url, "bob Journal"),
    ],
    ids=["signup", "invite_signup"],
)
def test_signup_ignores_a_posted_journal(
    client, main_user, second_user, url, journal_title
):
    client.post(
        url(main_user),
        SIGNUP | {"journal": second_user.journal.pk},
    )

    assert User.objects.get(username="john").journal.title == journal_title
