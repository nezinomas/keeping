from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, SearchMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = 'books/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'year': self.request.user.year,
            'tab': self.request.GET.get('tab'),
            'books': rendered_content(self.request, Lists),
            'chart': rendered_content(self.request, ChartReaded),
            'info': rendered_content(self.request, InfoRow),
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

    def readed(self):
        year = self.request.user.year
        qs = (models.Book.objects
              .readed()
              .filter(year=year)
        )
        return qs[0]['cnt'] if qs else 0

    def reading(self):
        year = self.request.user.year
        qs = (models.Book.objects
              .reading(year)
        )
        return qs['reading'] if qs else 0

    def target(self):
        year = self.request.user.year
        qs = None

        try:
            qs = (
                models.BookTarget.objects
                .related()
                .get(year=year)
            )
        except models.BookTarget.DoesNotExist:
            pass

        return qs if qs else 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'target': self.target(),
        })
        return context


class Lists(ListViewMixin):
    model = models.Book
    per_page = 50

    def get_queryset(self):
        tab = self.request.GET.get('tab')

        if tab:
            return\
                models.Book.objects \
                .items()

        return \
            models.Book.objects \
            .year(year=self.request.user.year)

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', 1)
        paginator = Paginator(self.get_queryset(), self.per_page)
        page_range = paginator.get_elided_page_range(number=page)

        context = super().get_context_data(**kwargs)
        context.update({
            'object_list': paginator.get_page(page),
            'url': reverse("books:list"),
            'page_range': page_range,
            'tab': self.request.GET.get('tab'),
        })
        return context


class New(CreateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    hx_trigger_django = 'reload'
    success_url = reverse_lazy('books:list')


class Update(UpdateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    hx_trigger_django = 'reload'
    success_url = reverse_lazy('books:list')


class Delete(DeleteViewMixin):
    model = models.Book
    hx_trigger_django = 'reload'
    success_url = reverse_lazy('books:list')


class Search(SearchMixin):
    template_name = 'books/book_list.html'
    per_page = 50

    search_method = 'search_books'


#----------------------------------------------------------------------------------------
#                                                                            Target Views
#----------------------------------------------------------------------------------------
class TargetNew(CreateViewMixin):
    model = models.BookTarget
    hx_trigger_django = 'afterTarget'
    form_class = forms.BookTargetForm
    url = reverse_lazy('books:target_new')


class TargetUpdate(UpdateViewMixin):
    model = models.BookTarget
    hx_trigger_django = 'afterTarget'
    form_class = forms.BookTargetForm
