from django.template.loader import render_to_string

from .. import models


def context_to_reload(request, year, context=None):
    context = context if context else {}

    readed = models.Book.objects.readed()
    reading = models.Book.objects.reading(year=year)

    context['chart_readed_books'] = render_to_string(
        'books/includes/chart_readed_books.html',
        {
            'categories': [x['year'] for x in readed],
            'data': [x['cnt'] for x in readed],
            'chart': 'chart_readed_books',
            'chart_title': 'Perskaitytos knygos',
            'chart_column_color': '70, 171, 157',
        },
        request
    )

    _readed = [x.get('cnt') for x in readed if x.get('year') == year]
    context['info_row'] = render_to_string(
        'books/includes/info_row.html',
        {
            'readed': _readed[0] if _readed else 0,
            'reading': reading[0]['cnt'] if reading else 0,
        },
        request
    )

    return context
