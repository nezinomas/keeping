from datetime import datetime

from crispy_forms.helper import FormHelper
from django import forms
from django.db.models import F
from django.db.models.functions import ExtractYear
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .apps import App_name
from .models import MAX_BOTTLES, Drink, DrinkTarget
from .services.model_services import DrinkModelService, DrinkTargetModelService


class DrinkForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Drink
        fields = ["user", "date", "quantity", "option"]

    field_order = ["date", "option", "quantity"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        # user input
        self.fields["user"].initial = self.user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

        # inital values
        self.fields["date"].initial = set_date_with_user_year(self.user)

        self.fields["date"].label = _("Date")
        self.fields["option"].label = _("Drink type")
        self.fields["quantity"].label = _("Quantity")

        _h1 = _("1 Beer = 0.5L")
        _h2 = _("1 Wine = 0.75L")
        _h3 = _("1 Vodka = 1L")
        _h4 = _("Millilitres are assumed if more than %(cnt)s is entered.") % {
            "cnt": MAX_BOTTLES
        }
        _help_text = f"{_h1}</br>{_h2}</br>{_h3}</br></br>{_h4}"
        self.fields["quantity"].help_text = _help_text

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.counter_type = App_name
        instance.save()

        return instance


class DrinkTargetForm(forms.ModelForm):
    class Meta:
        model = DrinkTarget
        fields = ["user", "year", "drink_type", "quantity"]

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year", "drink_type", "quantity"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # user input
        self.fields["user"].initial = self.user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

        # inital values
        self.fields["year"].initial = set_date_with_user_year(self.user).year

        self.fields["year"].label = _("Year")
        self.fields["quantity"].label = _("Quantity")
        self.fields["drink_type"].label = _("Drink type")

        _type = _("if the type of drink is")
        h1 = f"<b>ml</b> - {_type} {_('Beer')} / {_('Wine')} / {_('Vodka')}"
        h2 = f"<b>{_('pcs')}</b> - {_type} Std Av"
        help_text = f"{h1}</br>{h2}"
        self.fields["quantity"].help_text = help_text

    def clean_year(self):
        year = self.cleaned_data["year"]

        # if update
        if self.instance.pk:
            return year

        # if new record
        qs = DrinkTargetModelService(self.user).year(year)
        if qs.exists():
            msg = _("already has a goal.")
            raise forms.ValidationError(f"{year} {msg}")

        return year


class DrinkCompareForm(forms.Form):
    year1 = forms.IntegerField()
    year2 = forms.IntegerField()

    field_order = ["year1", "year2"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["year1"].label = None
        self.fields["year2"].label = None

        # inital values
        self.fields["year2"].initial = datetime.now().year

        self.helper = FormHelper()
        self.helper.form_show_labels = False

    def clean_year1(self):
        return self._clean_year_field("year1")

    def clean_year2(self):
        return self._clean_year_field("year2")

    def clean(self):
        cleaned = super().clean()
        year1 = cleaned.get("year1")
        year2 = cleaned.get("year2")

        years = (
            DrinkModelService(self.user)
            .items()
            .dates("date", "year")
            .annotate(year=ExtractYear(F("date")))
            .values_list("year", flat=True)
        )

        msg_no_records = _("No records this year")
        if year1 not in years and not self.errors.get("year1"):
            self.add_error("year1", msg_no_records)

        if year2 not in years and not self.errors.get("year2"):
            self.add_error("year2", msg_no_records)

        msg_different = _("Years must be different")
        if year1 == year2:
            self.add_error("year1", msg_different)
            self.add_error("year2", msg_different)

        return cleaned

    def _validation_error(self, field):
        if len(str(abs(field))) != 4:
            raise forms.ValidationError(_("Must be 4 digits."))

    def _clean_year_field(self, field_name):
        year = self.cleaned_data[field_name]
        self._validation_error(year)
        return year
