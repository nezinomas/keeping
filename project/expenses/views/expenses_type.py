from django.shortcuts import reverse, get_object_or_404

from ...core.mixins.save_data_mixin import SaveDataMixin
from ..forms import ExpenseNameForm, ExpenseTypeForm
from ..models import ExpenseName, ExpenseType


def _json_response(obj):
    obj.form_template = 'expenses/includes/partial_expenses_type_form.html'
    obj.items_template = 'expenses/includes/partial_expenses_type_list.html'
    obj.items_template_var_name = 'categories'
    obj.items = ExpenseType.objects.items()

    return obj.GenJsonResponse()


def new(request):
    form = ExpenseTypeForm(request.POST or None)
    context = {
        'url': reverse('expenses:expenses_type_new'),
        'action': 'insert',
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(ExpenseType, pk=pk)
    form = ExpenseTypeForm(request.POST or None, instance=object)
    url = reverse(
        'expenses:expenses_type_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)
