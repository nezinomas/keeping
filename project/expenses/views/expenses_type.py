from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, reverse

from ...core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from ..forms import ExpenseTypeForm
from ..models import ExpenseType


def settings():
    obj = CrudMixinSettings()

    obj.model = ExpenseType

    obj.form = ExpenseTypeForm
    obj.form_template = 'expenses/includes/expenses_type_form.html'

    obj.items_template = 'expenses/includes/expenses_type_list.html'
    obj.items_template_var_name = 'categories'

    obj.url_new = 'expenses:expenses_type_new'
    obj.url_update = 'expenses:expenses_type_update'

    return obj


@login_required()
def lists(request):
    return CrudMixin(request, settings()).lists_as_str()


@login_required()
def new(request):
    return CrudMixin(request, settings()).new()


@login_required()
def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
