from django.shortcuts import render

from ..core.mixins.views import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


class Lists(ListMixin):
    model = models.Account
    template_name = 'accounts/includes/accounts_list.html'

    def get_queryset(self):
        return models.Account.objects.related()


class New(CreateAjaxMixin):
    model = models.Account
    form_class = forms.AccountForm


class Update(UpdateAjaxMixin):
    model = models.Account
    form_class = forms.AccountForm

    def get_queryset(self):
        return models.Account.objects.related()

def load_to_account(request):
    _id = request.GET.get('id')
    objects = models.Account.objects.items().exclude(pk=_id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
