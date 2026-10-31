from django.utils.translation import gettext as _
from django.utils.translation import pgettext_lazy

# each key is the month's `?order=` value on a sortable Month table
MONTH_ABBREVIATIONS = (
    ("1", pgettext_lazy("month abbreviation", "Jan.")),
    ("2", pgettext_lazy("month abbreviation", "Feb.")),
    ("3", pgettext_lazy("month abbreviation", "Mar.")),
    ("4", pgettext_lazy("month abbreviation", "Apr.")),
    ("5", pgettext_lazy("month abbreviation", "May")),
    ("6", pgettext_lazy("month abbreviation", "Jun.")),
    ("7", pgettext_lazy("month abbreviation", "Jul.")),
    ("8", pgettext_lazy("month abbreviation", "Aug.")),
    ("9", pgettext_lazy("month abbreviation", "Sep.")),
    ("10", pgettext_lazy("month abbreviation", "Oct.")),
    ("11", pgettext_lazy("month abbreviation", "Nov.")),
    ("12", pgettext_lazy("month abbreviation", "Dec.")),
)


def month_names():
    return {
        "January": _("January"),
        "February": _("February"),
        "March": _("March"),
        "April": _("April"),
        "May": _("May"),
        "June": _("June"),
        "July": _("July"),
        "August": _("August"),
        "September": _("September"),
        "October": _("October"),
        "November": _("November"),
        "December": _("December"),
    }


def weekday_names():
    return {
        "Monday": _("Monday"),
        "Tuesday": _("Tuesday"),
        "Wednesday": _("Wednesday"),
        "Thursday": _("Thursday"),
        "Friday": _("Friday"),
        "Saturday": _("Saturday"),
        "Sunday": _("Sunday"),
    }
