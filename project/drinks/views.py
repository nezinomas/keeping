from django.shortcuts import get_object_or_404, render, reverse

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import DrinkForm
from .models import Drink


def settings():
    obj = CrudMixinSettings()

    obj.model = Drink

    obj.form = DrinkForm
    obj.form_template = 'drinks/includes/partial_drinks_form.html'

    obj.items_template = 'drinks/includes/partial_drinks_list.html'
    obj.items_template_main = 'drinks/drinks_list.html'

    obj.url_new = 'drinks:drinks_new'
    obj.url_update = 'drinks:drinks_update'

    return obj


def lists(request):
    return CrudMixin(request, settings()).lists_as_html()


def new(request):
    return CrudMixin(request, settings()).new()


def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
