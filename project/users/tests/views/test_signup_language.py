import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from ...models import User

pytestmark = pytest.mark.django_db

SIGNUP = {
    "username": "newbie",
    "email": "newbie@newbie.com",
    "password1": "Zq7!mxPl93k",
    "password2": "Zq7!mxPl93k",
}


def _sign_up(client, **headers):
    return client.post(reverse("users:signup"), SIGNUP, **headers)


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize("lang", ["lt", "en"])
def test_signup_journal_takes_accept_language(client, lang):
    _sign_up(client, HTTP_ACCEPT_LANGUAGE=lang)

    assert User.objects.get(username="newbie").journal.lang == lang


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize("cookie, accept", [("en", "lt"), ("lt", "en")])
def test_signup_journal_takes_language_cookie_over_accept_language(
    client, cookie, accept
):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie

    _sign_up(client, HTTP_ACCEPT_LANGUAGE=accept)

    assert User.objects.get(username="newbie").journal.lang == cookie


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize("lang", ["lt", "en"])
def test_signup_sets_the_language_cookie(client, lang):
    response = _sign_up(client, HTTP_ACCEPT_LANGUAGE=lang)

    cookie = response.cookies[settings.LANGUAGE_COOKIE_NAME]
    assert cookie.value == User.objects.get(username="newbie").journal.lang == lang
    assert cookie["max-age"] == settings.LANGUAGE_COOKIE_AGE


@override_settings(ENV={"CAN_SIGN_UP": True})
@pytest.mark.parametrize("lang", ["lt", "en"])
def test_signup_next_page_reads_that_language(client, lang):
    response = _sign_up(client, HTTP_ACCEPT_LANGUAGE=lang)

    follow = client.get(response["Location"])

    assert follow["Content-Language"] == lang
