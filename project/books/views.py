from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .lib.views_helper import BookRenderer


#----------------------------------------------------------------------------------------
#                                                                            Local Mixins
#----------------------------------------------------------------------------------------
def context_update(request, tab):
    context = {
        'tab': tab,
        'book_list': Lists.as_view()(request, as_string=True, tab=tab)
    }
    return context


class BookTabMixin():
    def get_tab(self):
        tab = self.request.GET.get("tab")

        if not tab:
            tab = self.kwargs.get('tab')

        tab = tab if tab in ['index', 'all'] else 'index'

        return tab

    def get_queryset(self):
        tab = self.get_tab()

        if tab == 'all':
            items = models.Book.objects.items()
        else:
            items = super().get_queryset()

        return items


class BookListMixin():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**context_update(self.request, self.get_tab()))

        return context


#----------------------------------------------------------------------------------------
#                                                                                   Views
#----------------------------------------------------------------------------------------
class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = BookRenderer(self.request, year)
        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'search': Search.as_view()(self.request, as_string=True),
            **obj.context_to_reload(),
            **context_update(self.request, 'index'),
        })
        return context


class All(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**context_update(self.request, 'all'))
        return context


class Lists(DispatchListsMixin, BookTabMixin, ListMixin):
    model = models.Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'tab': self.kwargs.get('tab')})
        return context


class New(BookListMixin, BookTabMixin, CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(BookListMixin, BookTabMixin, UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Delete(BookListMixin, BookTabMixin, DeleteAjaxMixin):
    model = models.Book


class ReloadStats(DispatchAjaxMixin, BookTabMixin, IndexMixin):
    template_name = 'books/index.html'
    redirect_view = reverse_lazy('books:books_index')

    def get(self, request, *args, **kwargs):
        tab = self.get_tab()
        context = context_update(self.request, tab)

        if tab == 'index':
            obj = BookRenderer(request)
            context.update(**obj.context_to_reload())

        return JsonResponse(context)


class Search(AjaxSearchMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    update_container = 'book_list'
    url = reverse_lazy('books:books_search')

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        _search = self.form_data_dict['search']
        context = {'items': None, 'tab': 'index' }
        sql = search.search_books(_search)

        if sql:
            context['items'] = sql
        else:
            context['notice'] = _('Found nothing')

        template = 'books/includes/books_list.html'
        html = render_to_string(template, context, self.request)

        kwargs.update({'container': 'book_list', 'html': html})

        return super().form_valid(form, **kwargs)

#----------------------------------------------------------------------------------------
#                                                                            Target Views
#----------------------------------------------------------------------------------------
class TargetLists(DispatchListsMixin, ListMixin):
    model = models.BookTarget


class TargetNew(CreateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm
