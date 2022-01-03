from datetime import datetime

from django.db.models.query import QuerySet


def chart_data(*args):
    items = {'categories': [], 'invested': [], 'profit': [], 'total': [], 'max': 0}

    for arr in args:
        if isinstance(arr, QuerySet):
            arr = list(arr)

        if not arr or not isinstance(arr, list):
            continue

        cnt = len(arr)
        for i in range(0, cnt):
            _y = arr[i]['year']
            _i= arr[i]['invested']
            _p = arr[i]['profit']
            _t = _i + _p

            if _y > datetime.now().year:
                continue

            if _i or _p:
                if _y not in items['categories']:
                    items['categories'].append(_y)
                    items['invested'].append(_i)
                    items['profit'].append(_p)
                    items['total'].append(_t)
                else:
                    ix = items['categories'].index(_y)  # category index
                    items['invested'][ix] += _i
                    items['profit'][ix] += _p
                    items['total'][ix] += _t

    # max value
    if items['profit'] or items['invested']:
        items['max'] = (max(items['profit']) + max(items['invested']))

    return items
