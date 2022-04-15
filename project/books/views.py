from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.get import GetQuerysetMixin
from ..core.mixins.views import CreateUpdateMixin, DeleteMixin
from . import forms, models


class Index(LoginRequiredMixin, TemplateView):
    template_name = 'books/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'year': self.request.user.year,
            'all': self.request.GET.get('tab'),
            'form': SearchForm(),
        })
        return context


class ChartReaded(LoginRequiredMixin, TemplateView):
    template_name = 'books/includes/chart_readed_books.html'

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


class InfoRow(LoginRequiredMixin, TemplateView):
    template_name = 'books/includes/info_row.html'

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


class Lists(LoginRequiredMixin, GetQuerysetMixin, ListView):
    model = models.Book
    template_name = 'books/includes/books_list.html'
    per_page = 50

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', 1)
        paginator = Paginator(self.get_queryset(), self.per_page)
        page_range = paginator.get_elided_page_range(number=page)

        context = super().get_context_data(**kwargs)
        context.update({
            'object_list': paginator.get_page(page),
            'url': reverse("books:books_list"),
            'page_range': page_range,
        })
        return context


class New(LoginRequiredMixin, CreateUpdateMixin, CreateView):
    model = models.Book
    form_class = forms.BookForm
    template_name = 'books/includes/books_form.html'
    success_url = reverse_lazy('books:books_list')

    url = reverse_lazy('books:books_new')
    form_action = 'insert'


class Update(LoginRequiredMixin, GetQuerysetMixin, CreateUpdateMixin, UpdateView):
    model = models.Book
    form_class = forms.BookForm
    template_name = 'books/includes/books_form.html'
    success_url = reverse_lazy('books:books_list')

    url = lambda self: self.object.get_absolute_url() if self.object else None
    form_action = 'update'


class Delete(LoginRequiredMixin, DeleteMixin, GetQuerysetMixin, DeleteView):
    model = models.Book
    template_name = 'books/includes/books_delete.html'
    success_url = reverse_lazy('books:books_list')

    url = lambda self: self.object.get_delete_url() if self.object else None


class Search(LoginRequiredMixin, TemplateView):
    template_name = 'books/includes/books_list.html'
    per_page = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({**self.search()})

        return context

    def search(self):
        search_str = self.request.GET.get('search')
        page = self.request.GET.get('page', 1)
        sql = search.search_books(search_str)
        context = {}

        if sql:
            paginator = Paginator(sql, self.per_page)
            page_range = paginator.get_elided_page_range(number=page)

            context.update({
                'object_list': paginator.get_page(page),
                'search': search_str,
                'url': reverse("books:books_search"),
                'page_range': page_range,
            })
        else:
            context.update({
                'object_list': None,
                'notice': _('Found nothing'),
            })

        return context


#----------------------------------------------------------------------------------------
#                                                                            Target Views
#----------------------------------------------------------------------------------------
class TargetNew(LoginRequiredMixin, CreateUpdateMixin, CreateView):
    template_name = 'books/includes/books_target_form.html'
    model = models.BookTarget
    form_class = forms.BookTargetForm

    url = reverse_lazy('books:books_target_new')
    form_action = 'insert'
    hx_trigger = 'afterTarget'


class TargetUpdate(LoginRequiredMixin, CreateUpdateMixin, GetQuerysetMixin, UpdateView):
    template_name = 'books/includes/books_target_form.html'
    model = models.BookTarget
    form_class = forms.BookTargetForm

    url = lambda self: self.object.get_absolute_url() if self.object else None
    form_action = 'update'
    hx_trigger = 'afterTarget'
