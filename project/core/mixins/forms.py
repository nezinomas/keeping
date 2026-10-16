from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..lib.date import latest_year, years


class YearBetweenMixin:
    def clean_date(self):
        dt = self.cleaned_data["date"]
        self.add_error_unless_year_between("date", years(self.user, self.today))

        return dt

    def add_error_unless_year_between(self, field, years_):
        if self.cleaned_data[field].year in years_:
            return

        self.add_error(
            field,
            _("Year must be between %(year1)s and %(year2)s")
            % ({"year1": years_[0], "year2": years_[-1]}),
        )


class OneTargetAYearMixin:
    # each form names its target_service: core imports no app

    def clean_year(self):
        year = self.cleaned_data["year"]

        if self.instance.pk:
            return year

        if self.target_service(self.user).year(year).exists():
            msg = _("%(year)s already has a goal.") % {"year": year}
            raise ValidationError(msg)

        return year


class ClosedYearMixin:
    # closed_fields = {field: (message with %(year)s, error field)}; core names no app

    def clean(self):
        cleaned = super().clean()
        dt = cleaned.get("date")
        if not dt:
            return cleaned

        for field, (message, error_field) in self.closed_fields.items():
            value = cleaned.get(field)
            if not value or not value.closed:
                continue
            if dt.year > value.closed:
                self.add_error(error_field, message % {"year": value.closed})
        return cleaned


class CloseNotBeforeRowsMixin:
    # each form names latest_row_year(): core names no app

    def clean_closed(self):
        closed = self.cleaned_data["closed"]
        if not closed:
            return closed

        latest = self.latest_row_year()
        if closed < latest:
            msg = _("Cannot close before %(year)s: there are records in that year.")
            raise ValidationError(msg % {"year": latest})

        return closed


class YearNotLaterMixin:
    def clean_date(self):
        dt = self.cleaned_data["date"]

        limit = latest_year(self.today)

        if dt.year > limit:
            self.add_error(
                "date",
                _("Year cannot be later than %(year)s") % {"year": limit},
            )

        return dt
