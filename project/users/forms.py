from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator

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


class InviteForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True
    )
    class Meta:
        fields = ('email')
