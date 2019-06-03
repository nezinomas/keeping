from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

# from ..core.mixins.save_data_mixin import SaveDataMixin
from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import AccountForm
from .models import Account


def settings():
    obj = CrudMixinSettings()

    obj.model = Account

    obj.form = AccountForm
    obj.form_template = 'accounts/includes/partial_accounts_form.html'

    obj.items_template = 'accounts/includes/partial_accounts_list.html'
    obj.items_template_var_name = 'categories'

    obj.url_new = 'accounts:accounts_new'
    obj.url_update = 'accounts:accounts_update'

    return obj


def lists(request):
    return CrudMixin(request, settings()).lists_as_str()


def new(request):
    return CrudMixin(request, settings()).new()


def update(request, pk):
    _settings = settings()
    _settings.item_id = pk

    return CrudMixin(request, _settings).update()


def load_to_account(request):
    id = request.GET.get('id')
    objects = Account.objects.exclude(pk=id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
