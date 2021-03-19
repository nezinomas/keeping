from django.template.loader import render_to_string

from .. import models


class BookRenderer():
    def __init__(self, request, year = None):
        self._request = request
        self._year = year if year else self._request.user.year

        self._qs_readed = models.Book.objects.readed()
        self._qs_reading = models.Book.objects.reading(self._year)
        self._qs_target = models.BookTarget.objects.year(self._year)

    def context_to_reload(self):
        context = {
            'info_row': self.render_info_row(),
            'chart_readed_books': self.render_chart_readed_books(),
        }
        return context

    def render_info_row(self):
        return render_to_string(
            'books/includes/info_row.html',
            self.context_info_row(),
            self._request
        )

    def context_info_row(self):
        readed = [x.get('cnt') for x in self._qs_readed if x.get('year') == self._year]
        context = {
            'readed': readed[0] if readed else 0,
            'reading': self._qs_reading['reading'] if self._qs_reading else 0,
            'target': self._qs_target[0] if self._qs_target else None,
        }
        return context

    def render_chart_readed_books(self):
        return render_to_string(
            'books/includes/chart_readed_books.html',
            self.context_chart_readed_books(),
            self._request
        )

    def context_chart_readed_books(self):
        context = {
            'categories': [x['year'] for x in self._qs_readed],
            'data': [x['cnt'] for x in self._qs_readed],
            'chart': 'chart_readed_books',
            'chart_title': 'Perskaitytos knygos',
            'chart_column_color': '70, 171, 157',
        }
        return context
