from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings

from .models import Saving, SavingType
from .forms import SavingForm, SavingTypeForm


# Saving views
def settings():
    obj = CrudMixinSettings()

    obj.model = Saving

    obj.form = SavingForm
    obj.form_template = 'savings/includes/partial_savings_form.html'

    obj.items_template = 'savings/includes/partial_savings_list.html'
    obj.items_template_main = 'savings/savings_list.html'

    obj.url_new = 'savings:savings_new'
    obj.url_update = 'savings:savings_update'

    return obj


def lists(request):
    context = {'categories': type_lists(request)}
    return CrudMixin(request, settings()).lists_as_html(context)


def new(request):
    return CrudMixin(request, settings()).new()


def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()


# Saving Type views
def type_settings():
    obj = CrudMixinSettings()

    obj.model = SavingType

    obj.form = SavingTypeForm
    obj.form_template = 'savings/includes/partial_savings_type_form.html'

    obj.items_template = 'savings/includes/partial_savings_type_list.html'
    obj.items_template_var_name = 'categories'

    obj.url_new = 'savings:savings_type_new'
    obj.url_update = 'savings:savings_type_update'

    return obj


def type_lists(request):
    return CrudMixin(request, type_settings()).lists_as_str()


def type_new(request):
    return CrudMixin(request, type_settings()).new()


def type_update(request, pk):
    _settings = type_settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
