from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .apps import App_name
from .lib.drink_quantity import DrinkQuantity
from .lib.drinks_options import MAX_BOTTLES
from .models import Drink, DrinkTarget
from .services.model_services import DrinkModelService, DrinkTargetModelService


class DrinkForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Drink
        fields = ["user", "date", "stdav", "option"]

    field_order = ["date", "option", "stdav"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set the counter type for the instance
        self.instance.counter_type = App_name

        self.date_field_settings()
        self.user_field_settings()
        self.translations()

        self.recalculate_stdav_on_opening_form()

    def date_field_settings(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user)

    def user_field_settings(self):
        self.fields["user"].initial = self.user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

    def translations(self):
        self.fields["date"].label = _("Date")
        self.fields["option"].label = _("Drink type")
        self.fields["stdav"].label = _("Quantity")

        self.fields["stdav"].help_text = render_to_string(
            "drinks/includes/drink_quantity_help.html", {"cnt": MAX_BOTTLES}
        )

    def recalculate_stdav_on_opening_form(self):
        if not self.instance.pk:
            return

        self.initial["stdav"] = self.instance.amount.value

    def clean(self):
        cleaned_data = super().clean()

        drink_type_input = cleaned_data.get("option")
        stdav_input = cleaned_data.get("stdav")

        if drink_type_input and stdav_input is not None:
            amount = DrinkQuantity.from_input(stdav_input, drink_type_input)
            cleaned_data["stdav"] = amount.stdav
            self.instance.converted_from_ml = amount.is_volume

        return cleaned_data


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

        # initial values
        self.fields["year"].initial = set_date_with_user_year(self.user).year

        self.user_field_settings()

        self.translations()

    def user_field_settings(self):
        self.fields["user"].initial = self.user
        self.fields["user"].disabled = True
        self.fields["user"].widget = forms.HiddenInput()

    def translations(self):
        self.fields["year"].label = _("Year")
        self.fields["quantity"].label = _("Quantity")
        self.fields["drink_type"].label = _("Drink type")

        self.fields["quantity"].help_text = render_to_string(
            "drinks/includes/drink_target_quantity_help.html"
        )

    def clean_year(self):
        year = self.cleaned_data["year"]

        # if update
        if self.instance.pk:
            return year

        # if new record
        qs = DrinkTargetModelService(self.user).year(year)
        if qs.exists():
            msg = _("%(year)s already has a goal.") % {"year": year}
            raise forms.ValidationError(msg)

        return year


class TypicalYearForm(forms.Form):
    year_from = forms.IntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2100)]
    )
    year_to = forms.IntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2100)]
    )

    field_order = ["year_from", "year_to"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # one query, read twice: the years propose the defaults here and decide
        # what is a real year in clean()
        self._years = DrinkModelService(self.user).years() if self.user else []

        self.fields["year_from"].label = ""
        self.fields["year_to"].label = ""

        if self._years:
            self.fields["year_from"].initial = self._years[0]
            self.fields["year_to"].initial = self._years[-1]

    def clean(self):
        cleaned = super().clean()
        year_from = cleaned.get("year_from")
        year_to = cleaned.get("year_to")

        years = self._years

        msg_no_records = _("No records this year")
        if year_from not in years and not self.errors.get("year_from"):
            self.add_error("year_from", msg_no_records)

        if year_to not in years and not self.errors.get("year_to"):
            self.add_error("year_to", msg_no_records)

        # a reversed range is a mistake to report, not one to correct: swapping
        # it would caption the chart with a span the user never asked for
        if year_from and year_to and year_from > year_to:
            self.add_error("year_from", _("Years must be in order"))

        return cleaned


class DrinkCompareForm(forms.Form):
    year1 = forms.IntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2100)]
    )
    year2 = forms.IntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2100)]
    )

    field_order = ["year1", "year2"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["year1"].label = ""
        self.fields["year2"].label = ""

        # inital values: the year in the header, which is not always the calendar
        # one — the user can be looking at a year that has not started yet
        self.fields["year2"].initial = (
            getattr(self.user, "year", None) or timezone.now().year
        )

    def clean(self):
        cleaned = super().clean()
        year1 = cleaned.get("year1")
        year2 = cleaned.get("year2")

        years = (
            DrinkModelService(self.user)
            .items()
            .values_list("date__year", flat=True)
            .order_by()
            .distinct()
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
