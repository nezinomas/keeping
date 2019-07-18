from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, reverse, render
from django.template.loader import render_to_string

from ..accounts.views import lists as accounts_list
from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import TransactionForm, SavingCloseForm
from .models import Transaction, SavingChange, SavingClose


def settings():
    obj = CrudMixinSettings()

    obj.model = Transaction

    obj.form = TransactionForm
    obj.form_template = 'transactions/includes/partial_transactions_form.html'

    obj.items_template = 'transactions/includes/partial_transactions_list.html'
    obj.items_template_main = 'transactions/transactions_list.html'

    obj.url_new = 'transactions:transactions_new'
    obj.url_update = 'transactions:transactions_update'

    return obj


@login_required()
def index(request):
    context = {
        'categories': accounts_list(request),
        'transactions': lists(request),
        'savings_close': savings_close_lists(request),
    }
    return CrudMixin(request, settings()).lists_as_html(context)


@login_required()
def lists(request):
    return CrudMixin(request, settings()).lists_as_str()


@login_required()
def new(request):
    return CrudMixin(request, settings()).new()


@login_required()
def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()


#
# Savings Transactions from Savings to regular Account
#
def close_settings():
    obj = CrudMixinSettings()

    obj.model = SavingClose

    obj.form = SavingCloseForm
    obj.form_template = 'transactions/includes/partial_savings_close_form.html'

    obj.items_template = 'transactions/includes/partial_savings_close.html'

    obj.url_new = 'transactions:savings_close_new'
    obj.url_update = 'transactions:savings_close_update'

    return obj


@login_required()
def savings_close_lists(request):
    return CrudMixin(request, close_settings()).lists_as_str()


@login_required()
def savings_close_new(request):
    return CrudMixin(request, close_settings()).new()


@login_required()
def savings_close_update(request, pk):
    _settings = close_settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()


#
# Savings Transactions betwenn Savings accounts
#
def change_settings():
    obj = CrudMixinSettings()

    obj.model = SavingChange

    # obj.form = TransactionForm
    # obj.form_template = 'transactions/includes/partial_transactions_form.html'

    # obj.items_template = 'transactions/includes/partial_transactions_list.html'
    # obj.items_template_main = 'transactions/transactions_list.html'

    # obj.url_new = 'transactions:transactions_new'
    # obj.url_update = 'transactions:transactions_update'

    return obj


@login_required()
def savings_change_lists(request):
    return CrudMixin(request, change_settings()).lists_as_str()


@login_required()
def savings_change_new(request):
    return CrudMixin(request, change_settings()).new()


@login_required()
def savings_change_update(request, pk):
    _settings = change_settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
