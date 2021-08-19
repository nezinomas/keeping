from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.forms import SearchForm
from .. import models


class BookRenderer():
    def __init__(self, request, year=None):
        self._request = request
        self._year = year if year else self._request.user.year

        self._qs_readed = models.Book.objects.readed()
        self._qs_reading = models.Book.objects.reading(self._year)
        self._qs_targets = models.BookTarget.objects.items()

    def context_to_reload(self):
        context = {
            'info_row': render_to_string(
                'books/includes/info_row.html',
                self.context_info_row(),
                self._request
            ),
            'chart_readed_books': render_to_string(
                'books/includes/chart_readed_books.html',
                self.context_chart_readed_books(),
                self._request
            ),
            'readed': self._qs_readed.count(),
        }
        return context

    def context_info_row(self):
        readed = [x.get('cnt') for x in self._qs_readed if x.get('year') == self._year]
        target = [x for x in self._qs_targets if x.year == self._year]

        context = {
            'readed': readed[0] if readed else 0,
            'reading': self._qs_reading['reading'] if self._qs_reading else 0,
            'target': target[0] if target else None,
        }

        return context

    def context_chart_readed_books(self):
        categories = []
        targets = []
        data = []
        for readed in self._qs_readed:
            # categories
            categories.append(readed['year'])

            # targets
            _target = 0
            for target in self._qs_targets:
                if target.year == readed['year']:
                    _target = target.quantity
            targets.append(_target)

            # data
            _data = {
                'y': readed['cnt'],
                'target': _target,
            }
            data.append(_data)

        context = {
            'categories': categories,
            'data': data,
            'targets': targets,
            'chart': 'chart_readed_books',
            'chart_title': _('Readed books'),
            'chart_column_color': '70, 171, 157',
        }
        return context

    def render_search_form(self):
        context = render_to_string(
            template_name='core/includes/search_form.html',
            context={
                'form': SearchForm(),
                'url': reverse('books:books_search')
            },
            request=self._request)

        return context
