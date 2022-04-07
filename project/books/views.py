from django.core.paginator import Paginator
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


class Search(AjaxSearchMixin):
    template_name = 'core/includes/search_form.html'
    list_template = 'books/includes/books_list.html'
    form_class = SearchForm
    form_data_dict = {}
    update_container = 'book_list'
    url = reverse_lazy('books:books_search')
    update_container = 'book_list'
    per_page = 25

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        search_str = self.form_data_dict['search']
        context = { 'tab': 'index' }
        sql = search.search_books(search_str)
        paginator = Paginator(sql, self.per_page)
        page_range = paginator.get_elided_page_range(number=1)

        if sql:
            context.update({
                'items': paginator.get_page(1),
                'search': search_str,
                'page_range': page_range,
                'url': self.url,
                'update_container': self.update_container,
            })
        else:
            context.update({
                'items': None,
                'notice': _('Found nothing'),
            })


        html = render_to_string(self.list_template, context, self.request)

        kwargs.update({'container': self.update_container, 'html': html})

        return super().form_valid(form, **kwargs)

    def get(self, request, *args, **kwargs):
        _page = request.GET.get('page')
        _search = request.GET.get('search')

        if _page and _search:
            sql = search.search_books(_search)
            paginator = Paginator(sql, self.per_page)
            page_range = paginator.get_elided_page_range(number=_page)

            context = {
                'tab': 'index',
                'items': paginator.get_page(_page),
                'search': _search,
                'page_range': page_range,
                'url': self.url,
                'update_container': self.update_container,
            }

            return JsonResponse(
                {self.update_container: render_to_string(self.list_template, context, self.request)}
            )

        return super().get(request, *args, **kwargs)


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
