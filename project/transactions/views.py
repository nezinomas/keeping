from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..accounts.views import Lists as accounts_list
from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin

from . import forms, models


@login_required()
def index(request):
    context = {
        'categories': accounts_list.as_view()(request, as_string=True),
        'transactions': Lists.as_view()(request, as_string=True),
        'savings_close': SavingsCloseLists.as_view()(request, as_string=True),
        'savings_change': SavingsChangeLists.as_view()(request, as_string=True),
    }
    return render(request, 'transactions/transactions_list.html', context)


# SavingType dropdown
def load_saving_type(request):
    id = request.GET.get('id')
    objects = models.SavingType.objects.exclude(pk=id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )


#
# Transactions between Accounts
#
class Lists(ListMixin):
    model = models.Transaction


class New(CreateAjaxMixin):
    model = models.Transaction
    form_class = forms.TransactionForm


class Update(UpdateAjaxMixin):
    model = models.Transaction
    form_class = forms.TransactionForm


#
# Savings Transactions from Savings to regular Accounts
#
class SavingsCloseLists(ListMixin):
    model = models.SavingClose


class SavingsCloseNew(CreateAjaxMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm


class SavingsCloseUpdate(UpdateAjaxMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm


#
# Savings Transactions between Savings accounts
#
class SavingsChangeLists(ListMixin):
    model = models.SavingChange


class SavingsChangeNew(CreateAjaxMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm


class SavingsChangeUpdate(UpdateAjaxMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
