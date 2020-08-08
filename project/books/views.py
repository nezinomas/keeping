from django.template.loader import render_to_string

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        context['book_list'] = Lists.as_view()(self.request, as_string=True)

        return context_to_reload(self.request, year, context)


class Lists(ListMixin):
    model = models.Book


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


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

    context['readed'] = _readed[0] if _readed else 0
    context['reading'] = reading[0]['cnt'] if reading else 0

    return context
