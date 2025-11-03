from django import forms
from django.utils.translation import gettext as _

from ..core.lib.form_widgets import YearPickerWidget
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["journal", "title", "closed", "order"]

    field_order = ["title", "order", "closed"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerWidget()

        # journal input
        self.fields["journal"].initial = user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Account title")
        self.fields["closed"].label = _("Closed")
        self.fields["order"].label = _("Sorting")
