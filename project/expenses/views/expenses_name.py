from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, reverse

from ...core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from ..forms import ExpenseNameForm
from ..models import ExpenseName, ExpenseType


def settings():
    obj = CrudMixinSettings()

    obj.model = ExpenseName

    obj.form = ExpenseNameForm
    obj.form_template = 'expenses/includes/expenses_name_form.html'

    obj.items_template = 'expenses/includes/expenses_type_list.html'
    obj.items_template_var_name = 'categories'

    obj.url_new = 'expenses:expenses_name_new'
    obj.url_update = 'expenses:expenses_name_update'

    return obj


@login_required()
def new(request):
    _settings = settings()
    _settings.model = ExpenseType

    return CrudMixin(request, _settings).new()


@login_required()
def update(request, pk):
    _settings = settings()
    _settings.item_id = pk
    _settings.items = ExpenseType.objects.all()

    return CrudMixin(request, _settings).update()
