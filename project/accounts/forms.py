from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..core.lib.form_fields import pin
from ..core.lib.form_widgets import YearPickerWidget
from ..core.mixins.forms import CloseNotBeforeRowsMixin, UserTodayMixin
from .models import Account
from .services.model_services import AccountModelService

ACCOUNT_CLOSED = gettext_lazy(
    "The date cannot be later than the account closure date. "
    "The account was closed in %(year)s."
)


class AccountForm(UserTodayMixin, CloseNotBeforeRowsMixin, forms.ModelForm):
    class Meta:
        model = Account
        fields = ["journal", "title", "closed", "order"]

    field_order = ["title", "order", "closed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_widgets()
        self._overwrite_default_queries()
        self._translate_fields()

    def _set_widgets(self):
        self.fields["closed"].widget = YearPickerWidget()

    def _overwrite_default_queries(self):
        pin(self.fields["journal"], self.user.journal)

    def _translate_fields(self):
        self.fields["title"].label = _("Account title")
        self.fields["closed"].label = _("Closed")
        self.fields["order"].label = _("Sorting")

    def latest_row_year(self):
        return AccountModelService(self.user).latest_row_year(self.instance)
