from django.shortcuts import render

from ..core.mixins.views import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


class Lists(ListMixin):
    model = models.Account
    template_name = 'accounts/includes/accounts_list.html'
    context_object_name = 'categories'


class New(CreateAjaxMixin):
    model = models.Account
    form_class = forms.AccountForm


class Update(UpdateAjaxMixin):
    model = models.Account
    form_class = forms.AccountForm


def load_to_account(request):
    id = request.GET.get('id')
    objects = models.Account.objects.exclude(pk=id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
