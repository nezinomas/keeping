from django import forms
from django.utils.translation import gettext as _

from ..core.lib.form_fields import pin
from ..core.lib.form_widgets import YearPickerWidget
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["journal", "title", "closed", "order"]

    field_order = ["title", "order", "closed"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerWidget()

        # journal input
        pin(self.fields["journal"], user.journal)

        self.fields["title"].label = _("Account title")
        self.fields["closed"].label = _("Closed")
        self.fields["order"].label = _("Sorting")
