from django.shortcuts import render
from django.views.generic.base import TemplateView

from ..accounts.views import Lists as accounts_list
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin, IndexMixin,
                                 ListMixin, UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = accounts_list.as_view()(
            self.request, as_string=True)
        context['transactions'] = Lists.as_view()(
            self.request, as_string=True)
        context['savings_close'] = SavingsCloseLists.as_view()(
            self.request, as_string=True)
        context['savings_change'] = SavingsChangeLists.as_view()(
            self.request, as_string=True)

        return context


# SavingType dropdown
class LoadSavingType(TemplateView):
    template_name = 'core/dropdown.html'

    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')

        objects = (models.SavingType
                   .objects
                   .items()
                   .exclude(pk=_id))

        return self.render_to_response({'objects': objects})


#----------------------------------------------------------------------------------------
#                                                           Transactions between Accounts
#----------------------------------------------------------------------------------------
class Lists(ListMixin):
    model = models.Transaction


class New(CreateAjaxMixin):
    model = models.Transaction
    form_class = forms.TransactionForm


class Update(UpdateAjaxMixin):
    model = models.Transaction
    form_class = forms.TransactionForm


class Delete(DeleteAjaxMixin):
    model = models.Transaction


#----------------------------------------------------------------------------------------
#                                   Savings Transactions from Savings to regular Accounts
#----------------------------------------------------------------------------------------
class SavingsCloseLists(ListMixin):
    model = models.SavingClose


class SavingsCloseNew(CreateAjaxMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm


class SavingsCloseUpdate(UpdateAjaxMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm


class SavingsCloseDelete(DeleteAjaxMixin):
    model = models.SavingClose


#----------------------------------------------------------------------------------------
#                                           Savings Transactions between Savings accounts
#----------------------------------------------------------------------------------------
class SavingsChangeLists(ListMixin):
    model = models.SavingChange


class SavingsChangeNew(CreateAjaxMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm


class SavingsChangeUpdate(UpdateAjaxMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm


class SavingsChangeDelete(DeleteAjaxMixin):
    model = models.SavingChange
