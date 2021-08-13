from datetime import datetime

from ..core.lib import utils
from ..counts.models import CountType
from .lib.date import yday as Yday
from .lib.date import year_month_list
from .lib.date import years as Year


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


def context_count_types(context):
    return {'context_count_types': list(CountType.objects.items())}
