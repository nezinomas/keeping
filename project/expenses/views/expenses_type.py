from django.shortcuts import render, reverse

from ...core.mixins.save_data_mixin import SaveDataMixin
from ..forms import ExpenseNameForm, ExpenseTypeForm
from ..models import ExpenseName, ExpenseType


def _items():
    qs = ExpenseType.objects.all().prefetch_related('expensename_set')
    return qs


def _json_response(obj):
    obj.form_template = 'expenses/includes/partial_expenses_type_form.html'
    obj.items_template = 'expenses/includes/partial_expenses_type_list.html'
    obj.items = _items()

    return obj.GenJsonResponse()


def lists(request):
    pass


def new(request):
    form = ExpenseTypeForm(request.POST or None)
    context = {'url': reverse('expenses:expenses_type_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    pass
