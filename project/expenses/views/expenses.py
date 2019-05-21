from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ...core.mixins.save_data_mixin import SaveDataMixin
from ..forms import ExpenseForm
from ..models import Expense, ExpenseName, ExpenseType


def _items():
    qs = Expense.objects.all().prefetch_related('expense_type', 'expense_name', 'account')
    return qs


def _json_response(obj):
    obj.form_template = 'expenses/includes/partial_expenses_form.html'
    obj.items_template = 'expenses/includes/partial_expenses_list.html'
    obj.items = _items()

    return obj.GenJsonResponse()


def lists(request):
    qs = _items()
    qse = ExpenseType.objects.all().prefetch_related('expensename_set')

    form = ExpenseForm(request=request)
    context = {'objects': qs, 'categories': qse, 'form': form}

    return render(request, 'expenses/expenses_list.html', context=context)


def new(request):
    form = ExpenseForm(data=(request.POST or None), request=request)
    context = {'url': reverse('expenses:expenses_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(data=(request.POST or None), instance=object, request=request)
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
    objects = (
        ExpenseName.objects.
        filter(parent_id=pk).
        filter(
            Q(valid_for__isnull=True) |
            Q(valid_for=request.session['year'])
        ).order_by('title')
    )
    return render(
        request,
        'expenses/expense_type_dropdown.html',
        {'objects': objects}
    )
