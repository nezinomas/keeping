import pytest

from ..factories import UserFactory
from ..forms import InviteForm, SignUpForm


# ---------------------------------------------------------------------------------------
#                                                                             Signup Form
# ---------------------------------------------------------------------------------------
def test_signup_form_init():
    SignUpForm()


def test_signup_form_inputs():
    form = SignUpForm()

    expected = ['username', 'email', 'password1', 'password2']
    actual = list(form.fields)

    assert expected == actual


@pytest.mark.django_db
def test_signup_unique_email():
    UserFactory()

    form = SignUpForm(data={
        'username': 'john',
        'email': 'bob@bob.com',
        'password1': 'abcdef123456',
        'password2': 'abcdef123456',
    })

    assert not form.is_valid()
    assert 'email' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                             Invite Form
# ---------------------------------------------------------------------------------------
def test_invite_form_init():
    InviteForm()


def test_invite_form_inputs():
    form = InviteForm()

    expected = ['email']
    actual = list(form.fields)

    assert expected == actual
