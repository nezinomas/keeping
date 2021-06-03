from django.views.generic import TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models


def context_to_reload(request):
    context = {
        'borrow': BorrowLists.as_view()(request, as_string=True),
        'lent': LentLists.as_view()(request, as_string=True),
    }
    return context


class ReloadIndex(DispatchAjaxMixin, TemplateView):
    template_name = 'debts/includes/reload_index.html'
    redirect_view = 'debts:debts_index'

    def get(self, request, *args, **kwargs):
        context = context_to_reload(self.request)
        return self.render_to_response(context=context)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'borrow_return': BorrowReturnLists.as_view()(self.request, as_string=True),
            'lent_return': LentReturnLists.as_view()(self.request, as_string=True),
            **context_to_reload(self.request)
        })
        return context


class BorrowLists(ListMixin):
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


class BorrowReturnLists(ListMixin):
    model = models.BorrowReturn


class BorrowReturnNew(CreateAjaxMixin):
    model = models.BorrowReturn
    form_class = forms.BorrowReturnForm


class BorrowReturnUpdate(UpdateAjaxMixin):
    model = models.BorrowReturn
    form_class = forms.BorrowReturnForm


class BorrowReturnDelete(DeleteAjaxMixin):
    model = models.BorrowReturn


class LentLists(ListMixin):
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


class LentReturnLists(ListMixin):
    model = models.LentReturn


class LentReturnNew(CreateAjaxMixin):
    model = models.LentReturn
    form_class = forms.LentReturnForm


class LentReturnUpdate(UpdateAjaxMixin):
    model = models.LentReturn
    form_class = forms.LentReturnForm


class LentReturnDelete(DeleteAjaxMixin):
    model = models.LentReturn
