import re

from crispy_forms.helper import FormHelper
from django import forms
from django.core.validators import (
    MaxLengthValidator,
    MinLengthValidator,
    RegexValidator,
)


class SearchForm(forms.Form):
    re_alphanumeric = re.compile(r"^[ _\w\d\.\-]+$", re.UNICODE)

    search = forms.CharField(
        validators=[
            MinLengthValidator(2),
            MaxLengthValidator(50),
            RegexValidator(re_alphanumeric, "Only alphabetic"),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["search"].label = None

        self.helper = FormHelper()
        self.helper.form_show_labels = False
