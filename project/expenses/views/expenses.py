from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ...core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from ..forms import ExpenseForm
from ..models import Expense, ExpenseName
from ..views.expenses_type import lists as type_lists


def settings():
    obj = CrudMixinSettings()

    obj.model = Expense

    obj.form = ExpenseForm
    obj.form_template = 'expenses/includes/partial_expenses_form.html'

    obj.items_template = 'expenses/includes/partial_expenses_list.html'
    obj.items_template_main = 'expenses/expenses_list.html'

    obj.url_new = 'expenses:expenses_new'
    obj.url_update = 'expenses:expenses_update'

    return obj


@login_required()
def lists(request):
    context = {'categories': type_lists(request)}
    return CrudMixin(request, settings()).lists_as_html(context)


@login_required()
def new(request):
    return CrudMixin(request, settings()).new()


@login_required()
def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = ExpenseName.objects.parent(pk).year(request.user.profile.year)

    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
