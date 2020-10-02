from django.http import JsonResponse
from django.shortcuts import reverse
from django.template.loader import render_to_string

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, DispatchAjaxMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .lib import views_helper as H


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'book_list': Lists.as_view()(self.request, as_string=True),
            'search': render_to_string(
                template_name='core/includes/search_form.html',
                context={
                    'form': SearchForm(),
                    'url': reverse('books:books_search')},
                request=self.request),
            **H.context_to_reload(self.request, context),
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
        return self.render_to_response(H.context_to_reload(request))


class Search(AjaxCustomFormMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}

    def form_valid(self, form):
        html = 'Nieko neradau'
        _search = self.form_data_dict['search']

        sql = search.search_books(_search)
        if sql:
            template = 'books/includes/books_list.html'
            context = {'items': sql}
            html = render_to_string(template, context, self.request)

        data = {
            'form_is_valid': True,
            'html_form': self._render_form({'form': form, 'url': reverse('books:books_search')}),
            'html': html,
        }
        return JsonResponse(data)
