import importlib

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from ....journals.tests.helpers import set_journal_lang

pytestmark = pytest.mark.django_db

COOKIE_FLAGS = ("max-age", "secure", "httponly", "samesite", "path", "domain")
HARDENED = {
    "LANGUAGE_COOKIE_AGE": 123,
    "LANGUAGE_COOKIE_SECURE": True,
    "LANGUAGE_COOKIE_HTTPONLY": True,
    "LANGUAGE_COOKIE_SAMESITE": "Strict",
    "LANGUAGE_COOKIE_DOMAIN": "example.com",
}


def _language_cookie(response):
    return response.cookies[settings.LANGUAGE_COOKIE_NAME]


def _flags(cookie):
    return {flag: cookie[flag] for flag in COOKIE_FLAGS}


def _login(client):
    return client.post(reverse("users:login"), {"username": "bob", "password": "123"})


def _save_settings(client, lang):
    url = reverse("users:settings_journal")
    return client.post(url, {"lang": lang, "title": "xxx"})


# Language cookie
def test_login_language_cookie_lives_as_long_as_configured(client):
    response = _login(client)

    assert _language_cookie(response)["max-age"] == settings.LANGUAGE_COOKIE_AGE


@override_settings(**HARDENED)
def test_login_and_settings_write_the_same_language_cookie(main_user, client):
    login = _login(client)
    saved = _save_settings(client, "lt")

    assert _flags(_language_cookie(login)) == _flags(_language_cookie(saved))
    assert _flags(_language_cookie(login)) == {
        "max-age": settings.LANGUAGE_COOKIE_AGE,
        "secure": settings.LANGUAGE_COOKIE_SECURE,
        "httponly": settings.LANGUAGE_COOKIE_HTTPONLY,
        "samesite": settings.LANGUAGE_COOKIE_SAMESITE,
        "path": settings.LANGUAGE_COOKIE_PATH,
        "domain": "example.com",
    }


def test_language_cookie_without_a_domain_has_an_empty_one(client):
    assert _language_cookie(_login(client))["domain"] == ""


def test_production_hardens_the_language_cookie():
    production = importlib.import_module("project.config.settings.production")
    hardened = {
        name: getattr(production, name)
        for name in (
            "LANGUAGE_COOKIE_SECURE",
            "LANGUAGE_COOKIE_HTTPONLY",
            "LANGUAGE_COOKIE_SAMESITE",
        )
    }

    assert hardened == {
        "LANGUAGE_COOKIE_SECURE": True,
        "LANGUAGE_COOKIE_HTTPONLY": True,
        "LANGUAGE_COOKIE_SAMESITE": "Strict",
    }


# Journal language
@pytest.mark.parametrize(
    "journal_lang, accept",
    [("lt", "en"), ("en", "lt")],
)
def test_journal_language_beats_accept_language(
    main_user, client_logged, journal_lang, accept
):
    set_journal_lang(main_user, journal_lang)

    response = client_logged.get(
        reverse("bookkeeping:index"), HTTP_ACCEPT_LANGUAGE=accept
    )

    assert response["Content-Language"] == journal_lang
    assert f'<html lang="{journal_lang}">' in response.content.decode()


@pytest.mark.parametrize(
    "journal_lang, label",
    [("lt", "Svetainės kalba"), ("en", "Journal language")],
)
def test_journal_language_translates_the_page(
    main_user, client_logged, journal_lang, label
):
    set_journal_lang(main_user, journal_lang)

    response = client_logged.get(
        reverse("users:settings_journal"), HTTP_ACCEPT_LANGUAGE="de"
    )

    assert label in response.content.decode()


@pytest.mark.parametrize("keep_cookie", [True, False])
@pytest.mark.parametrize("old, new", [("en", "lt"), ("lt", "en")])
def test_saved_language_applies_to_the_next_request(
    main_user, client_logged, old, new, keep_cookie
):
    set_journal_lang(main_user, old)
    _save_settings(client_logged, new)
    if not keep_cookie:
        del client_logged.cookies[settings.LANGUAGE_COOKIE_NAME]

    response = client_logged.get(reverse("bookkeeping:index"))

    assert response["Content-Language"] == new


@pytest.mark.parametrize("cookie, accept", [("en", "lt"), ("lt", "en")])
def test_anonymous_request_follows_the_cookie(client, cookie, accept):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie

    response = client.get(reverse("users:login"), HTTP_ACCEPT_LANGUAGE=accept)

    assert response["Content-Language"] == cookie
