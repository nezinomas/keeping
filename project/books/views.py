from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, TemplateViewMixin,
                                 UpdateViewMixin)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = 'books/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'year': self.request.user.year,
            'all': self.request.GET.get('tab'),
            'form': SearchForm(),
        })
        return context


class ChartReaded(TemplateViewMixin):
    template_name = 'books/chart_readed_books.html'

    def get_context_data(self, **kwargs):
        _qs_readed = models.Book.objects.readed()

        if not _qs_readed.count():
            self.template_name = 'empty.html'
            return {}

        _qs_targets = models.BookTarget.objects.items().values_list('year', 'quantity')

        _targets = {k: v for k, v in _qs_targets}

        categories = []
        targets = []
        data = []

        for readed in _qs_readed:
            _year = readed['year']

            # chart categories
            categories.append(_year)

            # chart targets
            _target = _targets.get(_year, 0)
            targets.append(_target)

            # chart serries data
            _data = {
                'y': readed['cnt'],
                'target': _target,
            }
            data.append(_data)

        context = super().get_context_data(**kwargs)
        context.update({
            'readed': _qs_readed.count(),
            'categories': categories,
            'data': data,
            'targets': targets,
            'chart': 'chart_readed_books',
            'chart_title': _('Readed books'),
            'chart_column_color': '70, 171, 157',
        })

        return context


class InfoRow(TemplateViewMixin):
    template_name = 'books/info_row.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year

        readed = models.Book.objects.readed().filter(year=year)
        reading = models.Book.objects.reading(year)['reading']
        target = models.BookTarget.objects.items().filter(year=year)

        context.update({
            'readed': readed[0]['cnt'] if readed else 0,
            'reading': reading if reading else 0,
            'target': target[0] if target else None,
        })

        return context


class Lists(ListViewMixin):
    model = models.Book
    per_page = 50

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', 1)
        paginator = Paginator(self.get_queryset(), self.per_page)
        page_range = paginator.get_elided_page_range(number=page)

        context = super().get_context_data(**kwargs)
        context.update({
            'object_list': paginator.get_page(page),
            'url': reverse("books:list"),
            'page_range': page_range,
        })
        return context


class New(CreateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    success_url = reverse_lazy('books:list')


class Update(UpdateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    success_url = reverse_lazy('books:list')


class Delete(DeleteViewMixin):
    model = models.Book
    success_url = reverse_lazy('books:list')


class Search(TemplateViewMixin):
    template_name = 'books/book_list.html'
    per_page = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({**self.search()})

        return context

    def search(self):
        search_str = self.request.GET.get('search')
        page = self.request.GET.get('page', 1)
        sql = search.search_books(search_str)
        context = {
            'object_list': None,
            'notice': _('Found nothing'),
        }

        if sql:
            paginator = Paginator(sql, self.per_page)
            page_range = paginator.get_elided_page_range(number=page)

            context.update({
                'object_list': paginator.get_page(page),
                'search': search_str,
                'url': reverse("books:search"),
                'page_range': page_range,
            })

        return context


#----------------------------------------------------------------------------------------
#                                                                            Target Views
#----------------------------------------------------------------------------------------
class TargetNew(CreateViewMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm

    url = reverse_lazy('books:target_new')
    form_action = 'insert'
    hx_trigger = 'afterTarget'


class TargetUpdate(UpdateViewMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm

    url = lambda self: self.object.get_absolute_url() if self.object else None
    form_action = 'update'
    hx_trigger = 'afterTarget'
