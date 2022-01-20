import json
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


def make_form_data_dict(form_data):
    _types = []
    _names = []
    _form_data_dict = {}
    _list = json.loads(form_data)

    # flatten list of dictionaries - form_data_list
    for field in _list:
        _field_name = field.get('name')
        _field_val = field.get('value')

        # expense type
        if _field_name == 'types' and not ':' in _field_val:
            _types.append(int(_field_val))
            continue

        # expense name
        if _field_name == 'types' and ':' in _field_val:
            _names.append(_field_val.split(':')[-1])
            continue

        # all other fields e.g. csrfmiddlewaretoke
        _form_data_dict[_field_name] = _field_val

    _form_data_dict['types'] = _types
    _form_data_dict['names'] = ','.join(_names)

    return _form_data_dict
