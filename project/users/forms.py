from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext as _

from ..core.lib import utils
from .models import User


class SignUpForm(UserCreationForm):
    email = forms.CharField(
        max_length=254,
        required=True,
        widget=forms.EmailInput()
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].label = _('Email')


class InviteForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True
    )
    class Meta:
        fields = ('email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].label = _('Email')

    def clean_email(self):
        email = self.cleaned_data['email']
        admin_email = utils.get_user().email

        if email == admin_email:
            raise ValidationError(_('You entered your own Email.'))

        emails = User.objects.exclude(email=admin_email).values_list('email', flat=True)
        if email in emails:
            raise ValidationError(_('User with this Email already exists.'))

        return email
