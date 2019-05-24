from django.shortcuts import get_object_or_404, render, reverse

from ..accounts.views import lists as accounts_list
from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import IncomeForm
from .models import Income


def _items(request):
    qs = (
        Income.objects.
        filter(date__year=request.session['year']).
        prefetch_related('account')
    )
    return qs


def _json_response(request, obj):
    obj.form_template = 'incomes/includes/partial_incomes_form.html'
    obj.items_template = 'incomes/includes/partial_incomes_list.html'

    obj.items = _items(request)

    return obj.GenJsonResponse()


def lists(request):
    qs = _items(request)

    form = IncomeForm(data={}, request=request)
    context = {
        'objects': qs,
        'categories': accounts_list(request),
        'form': form
    }

    return render(request, 'transactions/transactions_list.html', context=context)


def new(request):
    form = IncomeForm(data={request.POST or None}, request=request)
    context = {
        'url': reverse('incomes:incomes_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(Income, pk=pk)
    form = IncomeForm(data={request.POST or None}, instance=object, request=request)
    url = reverse(
        'incomes:incomes_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)
