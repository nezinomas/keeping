from django.template.loader import render_to_string
from django.urls import reverse_lazy

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, DispatchAjaxMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .lib import views_helper as H


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = H.BookRenderer(self.request, year)
        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'book_list': Lists.as_view()(self.request, as_string=True),
            'search': obj.render_search_form(),
            **obj.context_to_reload(),
        })
        return context


class Lists(ListMixin):
    model = models.Book


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class ReloadStats(DispatchAjaxMixin, IndexMixin):
    template_name = 'books/includes/reload_stats.html'
    redirect_view = 'books:books_index'

    def get(self, request, *args, **kwargs):
        obj = H.BookRenderer(request)
        return self.render_to_response(obj.context_to_reload())


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
            kwargs.update({'html': render_to_string(template, context, self.request)})

        return super().form_valid(form, **kwargs)


class TargetLists(ListMixin):
    model = models.BookTarget


class TargetNew(CreateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.BookTarget
    form_class = forms.BookTargetForm
