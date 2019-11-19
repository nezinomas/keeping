from .lib.date import years as Year


def years(context):
    _years = Year()

    return {'years': _years[::-1]}
