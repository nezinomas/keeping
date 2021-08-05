from ...core.mixins.views import (CreateAjaxMixin, DispatchListsMixin,
                                  ListMixin, UpdateAjaxMixin)
from .. import forms, models


class Lists(DispatchListsMixin, ListMixin):
    model = models.ExpenseType


class New(CreateAjaxMixin):
    model = models.ExpenseType
    form_class = forms.ExpenseTypeForm


class Update(UpdateAjaxMixin):
    model = models.ExpenseType
    form_class = forms.ExpenseTypeForm
