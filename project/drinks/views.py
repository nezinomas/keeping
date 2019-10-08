from ..core.mixins.views import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


class Lists(ListMixin):
    model = models.Drink
    template_name = 'drinks/index.html'


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
