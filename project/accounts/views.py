from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import AccountForm
from .models import Account


def _items():
    return Account.objects.all()


def _json_response(obj):
    obj.form_template = 'accounts/includes/partial_accounts_form.html'
    obj.items_template = 'accounts/includes/partial_accounts_list.html'

    obj.items = _items()
    obj.items_template_var_name = 'categories'

    return obj.GenJsonResponse()


def lists(request):
    qs = _items()
    return render_to_string(
        'accounts/includes/partial_accounts_list.html',
        {'categories': qs},
        request,
    )


def new(request):
    form = AccountForm(request.POST or None)
    context = {
        'url': reverse('accounts:accounts_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def update(request, pk):
    object = get_object_or_404(Account, pk=pk)
    form = AccountForm(request.POST or None, instance=object)
    url = reverse(
        'accounts:accounts_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(obj)


def load_to_account(request):
    id = request.GET.get('id')
    objects = Account.objects.exclude(pk=id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
