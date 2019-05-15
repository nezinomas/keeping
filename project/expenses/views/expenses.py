from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.template.loader import render_to_string

from ..forms import ExpenseForm
from ..helpers import helper_view_expenses as H_expenses
from ..models import Expense


def lists(request):
    qs = Expense.objects.all()
    form = ExpenseForm()
    context = {'objects': qs, 'form': form}

    return render(request, 'expenses/expenses_list.html', context=context)


def new(request):
    form = ExpenseForm(request.POST or None)
    context = {'url': reverse('expenses:expenses_new')}

    return H_expenses.save_data(request, context, form)


def update(request, pk):
    pass


def delete(request, pk):
    pass
