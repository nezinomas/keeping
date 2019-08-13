from ..core.mixins.ajax import AjaxCreateUpdateMixin
from ..core.mixins.crud import CreateMixin, ListMixin, UpdateMixin
from .forms import BookForm
from .models import Book


class BookMixin():
    model = Book
    form_class = BookForm
    template_name = 'books/includes/partial_books_form.html'


class Lists(ListMixin):
    model = Book
    template_name = 'books/books_list.html'


class New(BookMixin, AjaxCreateUpdateMixin, CreateMixin):
    pass


class Update(BookMixin, AjaxCreateUpdateMixin, UpdateMixin):
    pass
