from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..core.lib.form_fields import pin
from ..core.lib.form_widgets import YearPickerWidget
from .models import Account

ACCOUNT_CLOSED = gettext_lazy(
    "The date cannot be later than the account closure date. "
    "The account was closed in %(year)s."
)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["journal", "title", "closed", "order"]

    field_order = ["title", "order", "closed"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerWidget()

        pin(self.fields["journal"], user.journal)

        self.fields["title"].label = _("Account title")
        self.fields["closed"].label = _("Closed")
        self.fields["order"].label = _("Sorting")
