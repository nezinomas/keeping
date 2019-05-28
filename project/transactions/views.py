from django.shortcuts import get_object_or_404, reverse, render
from django.template.loader import render_to_string

from ..accounts.views import lists as accounts_list
from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import TransactionForm
from .models import Transaction


def _json_response(request, obj):
    obj.form_template = 'transactions/includes/partial_transactions_form.html'
    obj.items_template = 'transactions/includes/partial_transactions_list.html'
    obj.items = Transaction.objects.items(request.user.profile.year)

    return obj.GenJsonResponse()


def lists(request):
    qs = Transaction.objects.items(request.user.profile.year)

    form = TransactionForm()
    context = {
        'objects': qs,
        'categories': accounts_list(request),
        'form': form
    }

    return render(request, 'transactions/transactions_list.html', context=context)


def new(request):
    form = TransactionForm(request.POST or None)
    context = {'url': reverse('transactions:transactions_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Transaction, pk=pk)
    form = TransactionForm(request.POST or None, instance=object)
    url = reverse(
        'transactions:transactions_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)
