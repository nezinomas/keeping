from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models



def _debt_context_to_reload(request):
    context = {
        'debt': DebtLists.as_view()(request, as_string=True),
        'debt_return': DebtReturnLists.as_view()(request, as_string=True),
    }
    return context


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **_debt_context_to_reload(self.request),
        })
        return context


class DebtReload(LoginRequiredMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'debts/index.html'
    redirect_view = reverse_lazy('debts:debts_index')

    def get(self, request, *args, **kwargs):
        context = _debt_context_to_reload(self.request)
        return JsonResponse(context)


class DebtLists(DispatchListsMixin, ListMixin):
    model = models.Debt
    template_name = 'debts/includes/debts_list.html'


class DebtNew(CreateAjaxMixin):
    model = models.Debt
    form_class = forms.DebtForm
    list_render_output = False


class DebtUpdate(UpdateAjaxMixin):
    model = models.Debt
    form_class = forms.DebtForm
    list_render_output = False


class DebtDelete(DeleteAjaxMixin):
    model = models.Debt
    list_render_output = False


class DebtReturnLists(DispatchListsMixin, ListMixin):
    model = models.DebtReturn
    template_name = 'debts/includes/debts_return_list.html'


class DebtReturnNew(CreateAjaxMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm
    list_render_output = False


class DebtReturnUpdate(UpdateAjaxMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm
    list_render_output = False


class DebtReturnDelete(DeleteAjaxMixin):
    model = models.DebtReturn
    list_render_output = False
