from datetime import datetime


def years(context):
    now = datetime.now().year + 1
    years = [x for x in range(2004, now)]

    return {'years': years[::-1]}
