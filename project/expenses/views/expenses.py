from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ...core.mixins.save_data_mixin import SaveDataMixin
from ..forms import ExpenseForm
from ..models import Expense, ExpenseName, ExpenseType


def _json_response(request, obj):
    obj.form_template = 'expenses/includes/partial_expenses_form.html'
    obj.items_template = 'expenses/includes/partial_expenses_list.html'
    obj.items = Expense.objects.year_items(request.user.profile.year)

    return obj.GenJsonResponse()


@login_required()
def lists(request):
    qs = Expense.objects.year_items(request.user.profile.year)
    qse = ExpenseType.objects.items()

    form = ExpenseForm(data={}, request=request)
    context = {'objects': qs, 'categories': qse, 'form': form}

    return render(request, 'expenses/expenses_list.html', context=context)


@login_required()
def new(request):
    form = ExpenseForm(data=(request.POST or None), request=request)
    context = {'url': reverse('expenses:expenses_new'), 'action': 'insert'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


@login_required()
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

    return _json_response(request, obj)


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = ExpenseName.objects.items(pk, request.user.profile.year)

    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
