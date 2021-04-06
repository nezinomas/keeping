from django.shortcuts import render
from django.views.generic.base import TemplateView

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


class LoadAccount(TemplateView):
    template_name = 'core/dropdown.html'

    def get(self, request, *args, **kwargs):
        objects = []
        pk = request.GET.get('id')

        if pk:
            objects = (models.Account
                       .objects
                       .items()
                       .exclude(pk=pk))

        return self.render_to_response({'objects': objects})
