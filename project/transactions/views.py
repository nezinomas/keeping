from django.shortcuts import get_object_or_404, reverse, render
from django.template.loader import render_to_string

from ..accounts.views import lists as accounts_list
from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import TransactionForm
from .models import Transaction


def _items(request):
    qs = (
        Transaction.objects.
        filter(date__year=request.session['year']).
        prefetch_related('from_account', 'to_account')
    )
    return qs


def _json_response(request, obj):
    obj.form_template = 'transactions/includes/partial_transactions_form.html'
    obj.items_template = 'transactions/includes/partial_transactions_list.html'
    obj.items = _items(request)

    return obj.GenJsonResponse()


def lists(request):
    qs = _items(request)

    form = TransactionForm(request=request)
    context = {
        'objects': qs,
        'categories': accounts_list(request),
        'form': form
    }

    return render(request, 'transactions/transactions_list.html', context=context)


def new(request):
    form = TransactionForm(data=(request.POST or None), request=request)
    context = {'url': reverse('transactions:transactions_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Transaction, pk=pk)
    form = TransactionForm(
        data=(request.POST or None),
        instance=object,
        request=request
    )
    url = reverse(
        'transactions:transactions_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)
