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

    form = IncomeForm()
    context = {
        'objects': qs,
        'categories': accounts_list(request),
        'form': form
    }

    return render(request, 'incomes/incomes_list.html', context=context)


def new(request):
    form = IncomeForm(request.POST or None)
    context = {
        'url': reverse('incomes:incomes_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Income, pk=pk)
    form = IncomeForm(request.POST or None, instance=object)
    url = reverse(
        'incomes:incomes_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def type_lists(request):
    pass


def type_new(request):
    pass


def type_update(request, pk):
    pass
