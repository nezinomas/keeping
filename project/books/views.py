from django.shortcuts import redirect, render, reverse

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib import views_helper as H


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        context['book_list'] = Lists.as_view()(self.request, as_string=True)

        return H.context_to_reload(self.request, year, context)


class Lists(ListMixin):
    model = models.Book


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


def reload_stats(request):
    try:
        request.GET['ajax_trigger']
    except KeyError:
        return redirect(reverse('books:books_index'))

    return render(
        request=request,
        template_name='books/includes/reload_stats.html',
        context=H.context_to_reload(request, request.user.year)
    )
