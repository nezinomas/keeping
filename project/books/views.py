from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings

from .models import Book
from .forms import BookForm


def settings():
    obj = CrudMixinSettings()

    obj.model = Book

    obj.form = BookForm
    obj.form_template = 'books/includes/partial_books_form.html'

    obj.items_template = 'books/includes/partial_books_list.html'
    obj.items_template_main = 'books/books_list.html'

    obj.url_new = 'books:books_new'
    obj.url_update = 'books:books_update'

    return obj


def lists(request):
    return CrudMixin(request, settings()).lists_as_html()


def new(request):
    return CrudMixin(request, settings()).new()


def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
