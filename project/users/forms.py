from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .models import User


def refuse_taken_email(email):
    # casefold in Python: MariaDB's collation would also fold accents
    existing = {x.casefold() for x in User.objects.values_list("email", flat=True)}
    if email.casefold() in existing:
        raise ValidationError(_("User with this Email already exists."))


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].label = _("Email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        refuse_taken_email(email)
        return email


class InviteForm(forms.Form):
    email = forms.EmailField(max_length=User._meta.get_field("email").max_length)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["email"].label = _("Email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        admin_email = self.user.email

        if email.casefold() == admin_email.casefold():
            raise ValidationError(_("You entered your own Email."))

        refuse_taken_email(email)
        return email
