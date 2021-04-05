from datetime import datetime

from ..core.lib import utils
from .lib.date import yday as Yday
from .lib.date import years as Year, year_month_list


def years(context):
    _years = Year()

    return {'years': _years[::-1]}


def yday(context):
    _year = datetime.now().year
    try:
        _year = utils.get_user().year
    except AttributeError:
        pass

    _yday, _ydays = Yday(_year)

    return {'yday': _yday, 'ydays': _ydays}


def context_months(context):
    return {'context_months': year_month_list()}
