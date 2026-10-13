from django.utils.translation import gettext as _

from ..lib.date import latest_year, years


class YearBetweenMixin:
    def clean_date(self):
        dt = self.cleaned_data["date"]

        year_instance = dt.year
        years_ = years(self.user)

        if year_instance not in years_:
            self.add_error(
                "date",
                _("Year must be between %(year1)s and %(year2)s")
                % ({"year1": years_[0], "year2": years_[-1]}),
            )

        return dt


class YearNotLaterMixin:
    def clean_date(self):
        dt = self.cleaned_data["date"]

        limit = latest_year()

        if dt.year > limit:
            self.add_error(
                "date",
                _("Year cannot be later than %(year)s") % {"year": limit},
            )

        return dt
