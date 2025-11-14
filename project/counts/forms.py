from django import forms
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .models import Count, CountType
from .services.model_services import CountModelService, CountTypeModelService


class CountForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Count
        fields = ["user", "date", "quantity", "count_type"]

    field_order = ["date", "count_type", "quantity"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.counter_type = kwargs.pop("counter_type", None)

        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user)
        self.fields["quantity"].initial = 1

        if self.counter_type:
            obj = (
                CountTypeModelService(self.user)
                .objects.filter(slug=self.counter_type)
                .first()
            )
            self.fields["count_type"].initial = obj

        # initial value for user field
        self.fields["user"].initial = self.user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

    def _overwrite_default_queries(self):
        self.fields["count_type"].queryset = CountTypeModelService(self.user).items()

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["quantity"].label = _("Quantity")
        self.fields["count_type"].label = _("Count type")


class CountTypeForm(forms.ModelForm):
    class Meta:
        model = CountType
        fields = ["user", "title"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # user input
        self.fields["user"].initial = user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Title")

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
