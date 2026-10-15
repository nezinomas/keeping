from django import forms
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year, years_to_date
from ..core.lib.form_fields import pin
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import OneTargetAYearMixin, YearBetweenMixin
from .models import Book, BookTarget
from .services.model_services import BookTargetModelService


class BookForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = ["user", "started", "ended", "author", "title", "remark"]

    field_order = ["started", "ended", "author", "title", "remark"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self.fields["started"].widget = DatePickerWidget()
        self.fields["ended"].widget = DatePickerWidget()

        self.fields["started"].initial = set_date_with_user_year(self.user, self.today)

        pin(self.fields["user"], self.user)

        self.fields["started"].label = _("Started reading")
        self.fields["ended"].label = _("Ended reading")
        self.fields["title"].label = _("Title")
        self.fields["author"].label = _("Author")
        self.fields["remark"].label = _("Remark")

    def clean_started(self):
        dt = self.cleaned_data["started"]
        self.add_error_unless_year_between(
            "started", years_to_date(self.user, self.today)
        )

        if dt > self.today:
            self.add_error("started", _("Date cannot be in the future"))

        return dt

    def clean_ended(self):
        dt = self.cleaned_data["ended"]

        if dt and dt > self.today:
            self.add_error("ended", _("Date cannot be in the future"))

        return dt

    def clean(self):
        cleaned = super().clean()

        started = cleaned.get("started")
        ended = cleaned.get("ended")

        if ended and started and ended < started:
            self.add_error("ended", _("Finished reading cannot precede start reading."))

        return cleaned


class BookTargetForm(OneTargetAYearMixin, forms.ModelForm):
    target_service = BookTargetModelService

    class Meta:
        model = BookTarget
        fields = ["user", "year", "quantity"]

        widgets = {"year": YearPickerWidget()}

    field_order = ["year", "quantity"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        kwargs.pop("today")
        super().__init__(*args, **kwargs)

        pin(self.fields["user"], self.user)

        self.fields["year"].initial = self.user.year

        self.fields["year"].label = _("Year")
        self.fields["quantity"].label = _("How many")
