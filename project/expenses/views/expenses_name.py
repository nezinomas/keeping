from django.shortcuts import render, reverse, get_object_or_404

from ...core.mixins.save_data_mixin import SaveDataMixin
from ..forms import ExpenseNameForm
from ..models import ExpenseName, ExpenseType

TITLE = 'Išlaidų pavadinimas'


def _items():
    qs = ExpenseType.objects.all().prefetch_related('expensename_set')
    return qs


def _json_response(obj):
    obj.form_template = 'core/generic_form.html'
    obj.items_template = 'expenses/includes/partial_expenses_type_list.html'
    obj.items_template_var_name = 'categories'
    obj.items = _items()

    return obj.GenJsonResponse()


def new(request):
    form = ExpenseNameForm(request.POST or None)
    context = {
        'url': reverse('expenses:expenses_name_new'),
        'action': 'insert',
        'form_title': TITLE
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(ExpenseName, pk=pk)
    form = ExpenseNameForm(request.POST or None, instance=object)
    url = reverse(
        'expenses:expenses_name_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update', 'form_title': TITLE}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)
