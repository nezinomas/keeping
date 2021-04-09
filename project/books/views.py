from django.template.loader import render_to_string
from django.urls import reverse_lazy

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
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
            'search': obj.render_search_form(),
            **obj.context_to_reload(),
            **context_update(self.request, 'index'),
        })
        return context


class All(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**context_update(self.request, 'all'))
        return context


class Lists(BookTabMixin, ListMixin):
    model = models.Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'tab': self.kwargs.get('tab')})
        return context


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(BookListMixin, BookTabMixin, UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Delete(BookListMixin, BookTabMixin, DeleteAjaxMixin):
    model = models.Book


class ReloadStats(DispatchAjaxMixin, BookTabMixin, IndexMixin):
    template_name = 'books/includes/reload_stats.html'
    redirect_view = 'books:books_index'

    def get(self, request, *args, **kwargs):
        tab = self.get_tab()
        context = context_update(self.request, tab)

        if tab == 'index':
            obj = BookRenderer(request)
            context.update(**obj.context_to_reload())

        return self.render_to_response(context)


class Search(AjaxCustomFormMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('books:books_search')

    def form_valid(self, form, **kwargs):
        _search = self.form_data_dict['search']

        sql = search.search_books(_search)
        if sql:
            template = 'books/includes/books_list.html'
            context = {'items': sql}
            kwargs.update({
                'html': render_to_string(template, context, self.request),
                'container': 'book_list'
            })

        return super().form_valid(form, **kwargs)


#----------------------------------------------------------------------------------------
#                                                                            Target Views
#----------------------------------------------------------------------------------------
class TargetLists(ListMixin):
    model = models.BookTarget


class TargetNew(CreateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm
