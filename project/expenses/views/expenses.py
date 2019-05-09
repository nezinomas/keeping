from django.shortcuts import render
from ..models import Expense


def lists(request):
    qs = Expense.objects.all()
    context = {'objects': qs}

    return render(request, 'expenses/expenses_list.html', context=context)


def new(request):
    pass


def update(request, pk):
    pass


def delete(request, pk):
    pass
