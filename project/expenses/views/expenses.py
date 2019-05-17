from django.http import JsonResponse
from django.shortcuts import render, reverse, get_object_or_404
from django.template.loader import render_to_string

from ..forms import ExpenseForm
from ..helpers import helper_view_expenses as H_expenses
from ..models import Expense, ExpenseName


def lists(request):
    qs = Expense.objects.prefetch_related('expense_type', 'expense_name', 'account').all()
    form = ExpenseForm()
    context = {'objects': qs, 'form': form}

    return render(request, 'expenses/expenses_list.html', context=context)


def new(request):
    form = ExpenseForm(request.POST or None)
    context = {'url': reverse('expenses:expenses_new'), 'action': 'insert'}

    return H_expenses.save_data(request, context, form)


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
    return H_expenses.save_data(request, context, form)


def delete(request, pk):
    pass


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = ExpenseName.objects.filter(parent_id=pk).order_by('title')
    return render(
        request,
        'expenses/expense_type_dropdown.html',
        {'objects': objects}
    )
