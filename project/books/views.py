from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin

from .models import Book
from .forms import BookForm


def _items(request):
    qs = (
        Book.objects.
        filter(started__year=request.session['year'])
    )
    return qs


def _json_response(request, obj):
    obj.form_template = 'books/includes/partial_books_form.html'
    obj.items_template = 'books/includes/partial_books_list.html'

    obj.items = _items(request)

    return obj.GenJsonResponse()


def lists(request):
    qs = _items(request)

    form = BookForm()
    context = {
        'objects': qs,
        'form': form
    }

    return render(request, 'books/books_list.html', context=context)


def new(request):
    form = BookForm(request.POST or None)
    context = {
        'url': reverse('books:books_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, instance=object)
    url = reverse(
        'books:books_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)
