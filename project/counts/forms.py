from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..core.lib import form_utils, utils
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from .models import Count, CountType


class CountForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Count
        fields = ["user", "date", "quantity", "count_type"]

    field_order = ["date", "count_type", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

        form_utils.add_css_class(self)

        self.helper = FormHelper()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )
        self.fields["date"].initial = set_year_for_form()
        self.fields["quantity"].initial = 1

        if slug := utils.get_request_kwargs("slug"):
            obj = CountType.objects.filter(slug=slug).first()
            self.fields["count_type"].initial = obj

        # initial value for user field
        self.fields["user"].initial = utils.get_user()
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

    def _overwrite_default_queries(self):
        self.fields["count_type"].queryset = CountType.objects.items()

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["quantity"].label = _("Quantity")
        self.fields["count_type"].label = _("Count type")


class CountTypeForm(forms.ModelForm):
    class Meta:
        model = CountType
        fields = ["user", "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields["user"].initial = utils.get_user()
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Title")

        form_utils.add_css_class(self)

        self.helper = FormHelper()

    def clean_title(self):
        reserved_titles = [
            "none",
            "type",
            "delete",
            "update",
            "info_row",
            "index",
            "data",
            "history",
            "empty",
        ]
        title = self.cleaned_data["title"]

        if title and title.lower() in reserved_titles:
            self.add_error("title", _("This title is reserved for the system."))

        return title
