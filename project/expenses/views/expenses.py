from django.http import JsonResponse
from django.shortcuts import render, reverse, get_object_or_404
from django.template.loader import render_to_string

from ..forms import ExpenseForm
from ...core.mixins.save_data_mixin import SaveDataMixin
from ..models import Expense, ExpenseName, ExpenseType


def _items():
    qs = Expense.objects.all().prefetch_related('expense_type', 'expense_name', 'account')
    return qs


def _json_response(obj):
    obj.form_template = 'expenses/includes/partial_expenses_form_modal.html'
    obj.items_template = 'expenses/includes/partial_expenses_list.html'
    obj.items = _items()

    return obj.GenJsonResponse()


def lists(request):
    qs = _items()
    qse = ExpenseType.objects.all().prefetch_related('expensename_set')
    form = ExpenseForm()
    context = {'objects': qs, 'categories': qse, 'form': form}

    return render(request, 'expenses/expenses_list.html', context=context)


def new(request):
    form = ExpenseForm(request.POST or None)
    context = {'url': reverse('expenses:expenses_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=object)
    url = reverse(
        'expenses:expenses_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = ExpenseName.objects.filter(parent_id=pk).order_by('title')
    return render(
        request,
        'expenses/expense_type_dropdown.html',
        {'objects': objects}
    )
