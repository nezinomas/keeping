from datetime import datetime

from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import utils
from ..core.lib.convert_price import ConvertToPrice
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .models import SavingChange, SavingClose, SavingType, Transaction


class TransactionForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)

    class Meta:
        model = Transaction
        fields = ["date", "from_account", "to_account", "price"]

    field_order = ["date", "from_account", "to_account", "price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        # initial values
        self.fields["price"].widget.attrs = {"step": "0.01"}
        self.fields["price"].label = _("Amount")
        self.fields["date"].initial = set_date_with_user_year()

    def _overwrite_default_queries(self):
        from_account = self.fields["from_account"]
        to_account = self.fields["to_account"]

        from_account.queryset = Account.objects.items()
        to_account.queryset = Account.objects.none()

        _from = getattr(self.instance, "from_account", None)
        _from_pk = getattr(_from, "pk", None)
        if from_account_pk := self.data.get("from_account") or _from_pk:
            to_account.queryset = Account.objects.items().exclude(pk=from_account_pk)

    def _set_htmx_attributes(self):
        url = reverse("accounts:load")

        field = self.fields["from_account"]
        field.widget.attrs["hx-get"] = url
        field.widget.attrs["hx-target"] = "#id_to_account"
        field.widget.attrs["hx-trigger"] = "change"

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")


class SavingCloseForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)
    fee = forms.FloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingClose
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

        # if from_account is closed, update close checkbox value
        if hasattr(self.instance, "from_account") and self.instance.from_account.closed:
            self.fields["close"].initial = True

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year()

    def _overwrite_default_queries(self):
        self.fields["from_account"].queryset = SavingType.objects.items()
        self.fields["to_account"].queryset = Account.objects.items()

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")
        self.fields["close"].label = mark_safe(
            f"{_('Close')} <b>{_('From account')}</b>"
        )

    def save(self, *args, **kwargs):
        # update saving type if close checkbox is selected
        close = self.cleaned_data.get("close")

        obj = SavingType.objects.get(pk=self.instance.from_account.pk)
        if obj.closed and close:
            return super().save()

        obj.closed = self.instance.date.year if close else None
        obj.save()

        return super().save(*args, **kwargs)


class SavingChangeForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)
    fee = forms.FloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingChange
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

        # if from_account is closed, update close checkbox value
        if hasattr(self.instance, "from_account") and self.instance.from_account.closed:
            self.fields["close"].initial = True

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        # initial values
        self.fields["date"].initial = set_date_with_user_year()

    def _overwrite_default_queries(self):
        from_account = self.fields["from_account"]
        to_account = self.fields["to_account"]

        from_account.queryset = SavingType.objects.items()
        to_account.queryset = SavingType.objects.none()

        _from = getattr(self.instance, "from_account", None)
        _from_pk = getattr(_from, "pk", None)
        if from_account_pk := self.data.get("from_account") or _from_pk:
            to_account.queryset = SavingType.objects.items().exclude(pk=from_account_pk)

    def _set_htmx_attributes(self):
        url = reverse("transactions:load_saving_type")

        field = self.fields["from_account"]
        field.widget.attrs["hx-get"] = url
        field.widget.attrs["hx-target"] = "#id_to_account"
        field.widget.attrs["hx-trigger"] = "change"

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")
        self.fields["close"].label = mark_safe(
            f"{_('Close')} <b>{_('From account')}</b>"
        )

    def save(self, *args, **kwargs):
        # update related model if close checkbox selected
        close = self.cleaned_data.get("close")

        obj = SavingType.objects.get(pk=self.instance.from_account.pk)
        if obj.closed and close:
            return super().save()

        obj.closed = self.instance.date.year if close else None
        obj.save()

        return super().save(*args, **kwargs)
