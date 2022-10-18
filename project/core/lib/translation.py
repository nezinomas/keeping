from django.utils.translation import gettext as _


def month_names():
    return {
        'January': _('January'),
        'February': _('February'),
        'March': _('March'),
        'April': _('April'),
        'May': _('May'),
        'June': _('June'),
        'July': _('July'),
        'August': _('August'),
        'September': _('September'),
        'October': _('October'),
        'November': _('November'),
        'December': _('December')
    }

def weekday_names():
    return {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }
