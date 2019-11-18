from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.mixins.form_mixin import FormMixin
from .models import Account


class AccountForm(FormMixin, forms.ModelForm):
    class Meta:
        model = Account
        fields = ['title', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['title'].label = 'Sąskaitos pavadinimas'
        self.fields['order'].label = 'Rūšiavimas'
