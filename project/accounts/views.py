from django.urls import reverse_lazy

from ..core.mixins.views import (CreateViewMixin, ListViewMixin,
                                  UpdateViewMixin)
from . import forms, models


class Lists(ListViewMixin):
    model = models.Account

    def get_queryset(self):
        return models.Account.objects.related()


class New(CreateViewMixin):
    model = models.Account
    form_class = forms.AccountForm
    success_url = reverse_lazy('accounts:list')

    url = reverse_lazy('accounts:new')
    hx_trigger = 'afterAccount'


class Update(UpdateViewMixin):
    model = models.Account
    form_class = forms.AccountForm
    success_url = reverse_lazy('accounts:list')

    hx_trigger = 'afterAccount'

    def get_queryset(self):
        return models.Account.objects.related()


class LoadAccount(ListViewMixin):
    template_name = 'core/dropdown.html'
    object_list = []

    def get(self, request, *args, **kwargs):
        pk = request.GET.get('from_account')

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = None

        if pk:
            self.object_list = \
                models.Account \
                .objects \
                .items() \
                .exclude(pk=pk)

        return self.render_to_response({'object_list': self.object_list})
