from django.urls import reverse_lazy

from ...core.mixins.views import CreateViewMixin, UpdateViewMixin
from .. import forms, models


class QuerySetMixin():
    def get_queryset(self):
        return models.ExpenseType.objects.items()


class New(QuerySetMixin, CreateViewMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
    success_url = reverse_lazy('expenses:type_list')

    url = reverse_lazy('expenses:name_new')
    hx_trigger = 'afterName'


class Update(QuerySetMixin, UpdateViewMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
    success_url = reverse_lazy('expenses:type_list')

    hx_trigger = 'afterName'
