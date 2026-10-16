from datetime import date

import pytest

from ..forms import InviteForm, SignUpForm
from .factories import UserFactory

TODAY = date(1999, 2, 2)

SIGNUP = {
    "username": "john",
    "email": "john@john.com",
    "password1": "abcdef123456",
    "password2": "abcdef123456",
}

# a valid address one character longer than User.email holds
EMAIL_255 = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 59 + ".lt"


@pytest.mark.django_db
def test_signup_cleans_the_posted_values():
    form = SignUpForm(data=SIGNUP)

    assert form.is_valid()
    # a list, not a dict: the form asks in this order
    assert list(form.cleaned_data.items()) == list(SIGNUP.items())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email",
    ["bob@bob.com", "BOB@bob.com", "yan@y.yy", "bob@bób.com", "zoe@z.zz"],
    ids=[
        "email_exists",
        "email_exists_other_case",
        "email_stored_in_other_case",
        "email_exists_accented",
        "email_stored_accented",
    ],
)
def test_signup_unique_email(email):
    UserFactory()
    UserFactory(username="Yan", email="Yan@Y.yy")
    UserFactory(username="Zoe", email="Zoé@z.zz")

    form = SignUpForm(data=SIGNUP | {"email": email})

    assert not form.is_valid()
    assert form.errors["email"] == ["Vartotojas su šiuo Email jau egzistuoja."]


@pytest.mark.django_db
def test_invite_form_cleans_the_email(main_user):
    form = InviteForm(user=main_user, today=TODAY, data={"email": "New@New.com"})

    assert form.is_valid()
    assert form.cleaned_data == {"email": "New@New.com"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email, message",
    [
        ("bob@bob.com", "Įvedėte savo Email."),
        ("x@x.xx", "Vartotojas su šiuo Email jau egzistuoja."),
        ("BOB@bob.com", "Įvedėte savo Email."),
        ("bob@böb.com", "Įvedėte savo Email."),
        ("X@X.xx", "Vartotojas su šiuo Email jau egzistuoja."),
        ("yan@y.yy", "Vartotojas su šiuo Email jau egzistuoja."),
        ("x@ẍ.xx", "Vartotojas su šiuo Email jau egzistuoja."),
        (
            EMAIL_255,
            "Įsitikinkite, kad reikšmė sudaryta iš nedaugiau kaip 254 ženklų "
            "(dabartinis ilgis 255).",
        ),
        ("", "Šis laukas yra privalomas."),
    ],
    ids=[
        "same_as_admin_email",
        "email_exists",
        "same_as_admin_email_other_case",
        "same_as_admin_email_accented",
        "email_exists_other_case",
        "email_stored_in_other_case",
        "email_exists_accented",
        "email_longer_than_a_user_email",
        "email_missing",
    ],
)
def test_invite_form_refuses_an_email(main_user, second_user, email, message):
    UserFactory(username="Yan", email="Yan@Y.yy")
    form = InviteForm(user=main_user, today=TODAY, data={"email": email})

    assert not form.is_valid()
    assert form.errors["email"][0] == message
