from ..core.lib import utils
from .lib.date import yday as Yday
from .lib.date import years as Year


def years(context):
    _years = Year()

    return {'years': _years[::-1]}


def yday(context):
    _year = utils.get_user().year
    _yday, _ydays = Yday(_year)

    return {'yday': _yday, 'ydays': _ydays}
