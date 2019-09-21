from ..core.mixins.views import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import models, forms


class Lists(ListMixin):
    model = models.Book
    template_name = 'books/index.html'


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm
