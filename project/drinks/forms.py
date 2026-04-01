from datetime import datetime
from functools import cached_property

from crispy_forms.helper import FormHelper
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F
from django.db.models.functions import ExtractYear
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .apps import App_name
from .lib.drinks_options import MAX_BOTTLES, DrinksOptions
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

        _txt1 = _("1 Beer = 0.5L")
        _txt2 = _("1 Wine = 0.75L")
        _txt3 = _("1 Vodka = 1L")
        _txt4 = _("Millilitres are assumed if more than %(cnt)s is entered.") % {
            "cnt": MAX_BOTTLES
        }
        _help_text = f"{_txt1}<br>{_txt2}<br>{_txt3}<br><br>{_txt4}"
        self.fields["stdav"].help_text = mark_safe(_help_text)

    def recalculate_stdav_on_opening_form(self):
        if not self.instance.pk or self.instance.option == "stdav":
            return

        options = DrinksOptions(drink_type=self.instance.option)
        if self.instance.converted_from_ml:
            val = options.stdav_to_ml(
                drink_type=self.instance.option, stdav=self.instance.stdav
            )
        else:
            val = self.instance.stdav * options.ratio

        self.initial["stdav"] = val

    def recalculate_stdav_on_save(self):
        converted = False

        if self.instance.option == "stdav":
            return self.instance.stdav, converted

        options = DrinksOptions(drink_type=self.instance.option)

        if self.instance.stdav > MAX_BOTTLES:
            stdav = options.ml_to_stdav(
                drink_type=self.instance.option, ml=self.instance.stdav
            )
            converted = True
        else:
            stdav = self.instance.stdav / options.ratio

        return stdav, converted

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)

        instance.counter_type = App_name
        instance.stdav, instance.converted_from_ml = self.recalculate_stdav_on_save()

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

        # inital values
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

        _type = _("if the type of drink is")
        _txt1 = f"<b>ml</b> - {_type} {_('Beer')} / {_('Wine')} / {_('Vodka')}"
        _txt2 = f"<b>{_('pcs')}</b> - {_type} Std Av"
        _txt3 = f"{_txt1}</br>{_txt2}"

        self.fields["quantity"].help_text = mark_safe(_txt3)

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

        self.fields["year1"].label = None
        self.fields["year2"].label = None

        # inital values
        self.fields["year2"].initial = datetime.now().year

    @cached_property
    def helper(self):
        helper = FormHelper()
        helper.form_show_labels = False
        return helper

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
