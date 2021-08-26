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


def _lent_context_to_reload(request):
    context = {
        'lent': LentLists.as_view()(request, as_string=True),
        'lent_return': LentReturnLists.as_view()(request, as_string=True),
    }
    return context


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **_borrow_context_to_reload(self.request),
            **_lent_context_to_reload(self.request),
        })
        return context


class BorrowReload(DispatchAjaxMixin, TemplateView):
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


class LentReload(DispatchAjaxMixin, TemplateView):
    template_name = 'debts/index.html'
    redirect_view = reverse_lazy('debts:debts_index')

    def get(self, request, *args, **kwargs):
        context = _lent_context_to_reload(self.request)
        return JsonResponse(context)


class LentLists(DispatchListsMixin, ListMixin):
    model = models.Lent
    template_name = 'debts/includes/lents_list.html'


class LentNew(CreateAjaxMixin):
    model = models.Lent
    form_class = forms.LentForm
    list_render_output = False


class LentUpdate(UpdateAjaxMixin):
    model = models.Lent
    form_class = forms.LentForm
    list_render_output = False


class LentDelete(DeleteAjaxMixin):
    model = models.Lent
    list_render_output = False


class LentReturnLists(DispatchListsMixin, ListMixin):
    model = models.LentReturn
    template_name = 'debts/includes/lents_return_list.html'


class LentReturnNew(CreateAjaxMixin):
    model = models.LentReturn
    form_class = forms.LentReturnForm
    list_render_output = False


class LentReturnUpdate(UpdateAjaxMixin):
    model = models.LentReturn
    form_class = forms.LentReturnForm
    list_render_output = False


class LentReturnDelete(DeleteAjaxMixin):
    model = models.LentReturn
    list_render_output = False
