from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import IncomeForm, IncomeTypeForm
from .models import Income, IncomeType


def settings():
    obj = CrudMixinSettings()

    obj.model = Income

    obj.form = IncomeForm
    obj.form_template = 'incomes/includes/partial_incomes_form.html'

    obj.items_template = 'incomes/includes/partial_incomes_list.html'
    obj.items_template_main = 'incomes/incomes_list.html'

    obj.url_new = 'incomes:incomes_new'
    obj.url_update = 'incomes:incomes_update'

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


# IncomeType helper functions and views
def type_settings():
    obj = CrudMixinSettings()

    obj.model = IncomeType

    obj.form = IncomeTypeForm
    obj.form_template = 'incomes/includes/partial_incomes_type_form.html'

    obj.items_template = 'incomes/includes/partial_incomes_type_list.html'
    obj.items_template_var_name = 'categories'

    obj.url_new = 'incomes:incomes_type_new'
    obj.url_update = 'incomes:incomes_type_update'

    return obj


def type_lists(request):
    return CrudMixin(request, type_settings()).lists_as_str()


def type_new(request):
    return CrudMixin(request, type_settings()).new()


def type_update(request, pk):
    _settings = type_settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
