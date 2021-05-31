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


class BorrowReturnLists(ListMixin):
    model = models.BorrowReturn


class LentLists(ListMixin):
    model = models.Lent


class LentReturnLists(ListMixin):
    model = models.LentReturn
