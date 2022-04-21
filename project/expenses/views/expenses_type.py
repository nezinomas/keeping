from django.urls import reverse_lazy

from ...core.mixins.views import (CreateViewMixin, ListViewMixin,
                                  UpdateViewMixin)
from .. import forms, models


class Lists(ListViewMixin):
    model = models.ExpenseType


class New(CreateViewMixin):
    model = models.ExpenseType
    form_class = forms.ExpenseTypeForm
    success_url = reverse_lazy('expenses:type_list')

    url = reverse_lazy('expenses:type_new')
    hx_trigger = 'afterType'


class Update(UpdateViewMixin):
    model = models.ExpenseType
    form_class = forms.ExpenseTypeForm
    success_url = reverse_lazy('expenses:type_list')

    hx_trigger = 'afterType'
