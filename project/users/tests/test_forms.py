from ..forms import InviteForm, SignUpForm


def test_signup_form_init():
    SignUpForm()


def test_signup_form_inputs():
    form = SignUpForm()

    expected = ['username', 'email', 'password1', 'password2']
    actual = list(form.fields)

    assert expected == actual


def test_invite_form_init():
    InviteForm()


def test_invite_form_inputs():
    form = InviteForm()

    expected = ['email']
    actual = list(form.fields)

    assert expected == actual
