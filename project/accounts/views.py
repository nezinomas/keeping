from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView

from ..core.lib import utils
from ..core.mixins.views import (CreateAjaxMixin, DispatchListsMixin,
                                 ListMixin, UpdateAjaxMixin)
from . import forms, models


class Lists(DispatchListsMixin, ListMixin):
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


class LoadAccount(LoginRequiredMixin, TemplateView):
    template_name = 'core/dropdown.html'

    def dispatch(self, request, *args, **kwargs):
        if not utils.is_ajax(self.request):
            return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        objects = []
        pk = request.GET.get('id')

        if pk:
            objects = (models
                       .Account
                       .objects
                       .items()
                       .exclude(pk=pk))

        return self.render_to_response({'objects': objects})
