from django import forms
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import pin
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import UserTodayMixin, YearBetweenMixin
from .models import Count, CountType
from .services.model_services import CountTypeModelService


class CountForm(UserTodayMixin, YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Count
        fields = ["user", "date", "quantity", "count_type"]

    field_order = ["date", "count_type", "quantity"]

    def __init__(self, *args, **kwargs):
        self.counter_type = kwargs.pop("counter_type", "")

        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)
        self.fields["quantity"].initial = 1

        if self.counter_type:
            obj = (
                CountTypeModelService(self.user)
                .objects.filter(slug=self.counter_type)
                .first()
            )
            self.fields["count_type"].initial = obj

        pin(self.fields["user"], self.user)

    def _overwrite_default_queries(self):
        self.fields["count_type"].queryset = CountTypeModelService(self.user).items()

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["quantity"].label = _("Quantity")
        self.fields["count_type"].label = _("Count type")


class CountTypeForm(UserTodayMixin, forms.ModelForm):
    class Meta:
        model = CountType
        fields = ["user", "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pin(self.fields["user"], self.user)

        self.fields["title"].label = _("Title")
