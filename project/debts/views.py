from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from ..core.lib import utils
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models


def _borrow_context_to_reload(request):
    try:
        request.resolver_match.kwargs['debt_type'] = 'borrow'
    except AttributeError:
        pass

    context = {
        'borrow': DebtLists.as_view()(request, as_string=True),
        'borrow_return': DebtReturnLists.as_view()(request, as_string=True),
    }
    return context


def _lend_context_to_reload(request):
    try:
        request.resolver_match.kwargs['debt_type'] = 'lend'
    except AttributeError:
        pass

    context = {
        'lend': DebtLists.as_view()(request, as_string=True),
        'lend_return': DebtReturnLists.as_view()(request, as_string=True),
    }
    return context


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **_lend_context_to_reload(self.request),
            **_borrow_context_to_reload(self.request),
        })
        return context


class DebtReload(LoginRequiredMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'debts/index.html'
    redirect_view = reverse_lazy('debts:debts_index')

    def get(self, request, *args, **kwargs):
        _context = {}
        _type = self.kwargs.get('debt_type')

        if _type == 'lend':
            _context.update({**_lend_context_to_reload(self.request)})

        if _type == 'borrow':
            _context.update({**_borrow_context_to_reload(self.request)})

        return JsonResponse(_context)


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
