from ..core.mixins.views import (CreateAjaxMixin, DispatchAjaxMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .lib import views_helper as H


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['book_list'] = Lists.as_view()(self.request, as_string=True)

        return H.context_to_reload(self.request, context)


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
