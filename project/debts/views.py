from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin, IndexMixin,
                                 ListMixin, UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["borrow"] = BorrowLists.as_view()(self.request, as_string=True)
        context["borrow_return"] = BorrowReturnLists.as_view()(self.request, as_string=True)
        context["lent"] = LentLists.as_view()(self.request, as_string=True)
        context["lent_return"] = LentReturnLists.as_view()(self.request, as_string=True)

        return context


class BorrowLists(ListMixin):
    model = models.Borrow


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
