import pytest

from ..forms import InviteForm, SignUpForm
from .factories import UserFactory


def test_signup_form_inputs():
    form = SignUpForm()

    expected = ["username", "email", "password1", "password2"]
    actual = list(form.fields)

    assert expected == actual


@pytest.mark.django_db
def test_signup_unique_email():
    UserFactory()

    form = SignUpForm(
        data={
            "username": "john",
            "email": "bob@bob.com",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
        }
    )

    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.django_db
def test_invite_form_inputs(main_user):
    form = InviteForm(user=main_user)

    expected = ["email"]
    actual = list(form.fields)

    assert expected == actual


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email, message",
    [
        ("bob@bob.com", "Įvedėte savo Email."),
        ("x@x.xx", "Vartotojas su šiuo Email jau egzistuoja."),
    ],
    ids=["same_as_admin_email", "email_exists"],
)
def test_invite_form_refuses_an_email(main_user, second_user, email, message):
    form = InviteForm(user=main_user, data={"email": email})

    assert not form.is_valid()
    assert "email" in form.errors
    assert form.errors["email"][0] == message
