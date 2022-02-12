from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models


def _borrow_context_to_reload(request):
    context = {
        'borrow': BorrowLists.as_view()(request, as_string=True),
        'borrow_return': BorrowReturnLists.as_view()(request, as_string=True),
    }
    return context


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
            **_borrow_context_to_reload(self.request),
            **_debt_context_to_reload(self.request),
        })
        return context


class BorrowReload(LoginRequiredMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'debts/index.html'
    redirect_view = reverse_lazy('debts:debts_index')

    def get(self, request, *args, **kwargs):
        context = _borrow_context_to_reload(self.request)
        return JsonResponse(context)


class BorrowLists(DispatchListsMixin, ListMixin):
    model = models.Borrow
    template_name = 'debts/includes/borrows_list.html'


class BorrowNew(CreateAjaxMixin):
    model = models.Borrow
    form_class = forms.BorrowForm
    list_render_output = False


class BorrowUpdate(UpdateAjaxMixin):
    model = models.Borrow
    form_class = forms.BorrowForm
    list_render_output = False


class BorrowDelete(DeleteAjaxMixin):
    model = models.Borrow
    list_render_output = False


class BorrowReturnLists(DispatchListsMixin, ListMixin):
    model = models.BorrowReturn
    template_name = 'debts/includes/borrows_return_list.html'


class BorrowReturnNew(CreateAjaxMixin):
    model = models.BorrowReturn
    form_class = forms.BorrowReturnForm
    list_render_output = False


class BorrowReturnUpdate(UpdateAjaxMixin):
    model = models.BorrowReturn
    form_class = forms.BorrowReturnForm
    list_render_output = False


class BorrowReturnDelete(DeleteAjaxMixin):
    model = models.BorrowReturn
    list_render_output = False


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
