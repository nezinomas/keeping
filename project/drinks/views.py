from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


class Lists(ListMixin):
    model = models.Drink
    template_name = 'drinks/drinks_list.html'


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm
