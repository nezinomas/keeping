from ..forms import SignUpForm


def test_signup_form_init():
    SignUpForm()


def test_signup_form_inputs():
    form = SignUpForm()

    expected = ['username', 'email', 'password1', 'password2']
    actual = list(form.fields)

    assert expected == actual
