from django.template.loader import render_to_string

from .. import models


def context_to_reload(request, context=None):
    context = context if context else {}
    year = request.user.year

    qs_readed = models.Book.objects.readed()
    qs_reading = models.Book.objects.reading()

    context['chart_readed_books'] = render_to_string(
        'books/includes/chart_readed_books.html',
        {
            'categories': [x['year'] for x in qs_readed],
            'data': [x['cnt'] for x in qs_readed],
            'chart': 'chart_readed_books',
            'chart_title': 'Perskaitytos knygos',
            'chart_column_color': '70, 171, 157',
        },
        request
    )

    readed = [x.get('cnt') for x in qs_readed if x.get('year') == year]
    context['info_row'] = render_to_string(
        'books/includes/info_row.html',
        {
            'readed': readed[0] if readed else 0,
            'reading': qs_reading['reading'] if qs_reading else 0,
        },
        request
    )

    return context
