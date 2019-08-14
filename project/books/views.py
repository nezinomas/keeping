from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import models, forms


class Lists(ListMixin):
    model = models.Book
    template_name = 'books/books_list.html'


class New(CreateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm


class Update(UpdateAjaxMixin):
    model = models.Book
    form_class = forms.BookForm
