import re

from crispy_forms.helper import FormHelper
from django import forms
from django.core.validators import (MaxLengthValidator, MinLengthValidator,
                                    RegexValidator)

from .helpers.helper_forms import add_css_class


class SearchForm(forms.Form):
    re_alphanumeric = re.compile(r"^[ _\w\d\.\-]+$", re.UNICODE)

    search = forms.CharField(validators=[
        MinLengthValidator(2),
        MaxLengthValidator(50),
        RegexValidator(re_alphanumeric, 'Only alphabetic')
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['search'].label = None

        self.helper = FormHelper()
        add_css_class(self, self.helper)
