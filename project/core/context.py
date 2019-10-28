from datetime import datetime

from .lib.date import years as Year


def years(context):
    years = Year()

    return {'years': years[::-1]}
