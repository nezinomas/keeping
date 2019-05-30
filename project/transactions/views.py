from django.shortcuts import get_object_or_404, reverse, render
from django.template.loader import render_to_string

from ..accounts.views import lists as accounts_list
from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import TransactionForm
from .models import Transaction


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


def lists(request):
    context = {'categories': accounts_list(request)}
    return CrudMixin(request, settings()).lists_as_html(context)


def new(request):
    return CrudMixin(request, settings()).new()


def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()
