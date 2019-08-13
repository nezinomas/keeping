from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.ajax import AjaxCreateUpdateMixin
from ..core.mixins.crud import CreateMixin, ListMixin, UpdateMixin
from .forms import AccountForm
from .models import Account


class AccountMixin():
    model = Account
    form_class = AccountForm
    template_name = 'accounts/includes/partial_accounts_form.html'


class Lists(ListMixin):
    model = Account
    template_name = 'accounts/includes/partial_accounts_list.html'
    context_object_name = 'categories'


class New(AccountMixin, AjaxCreateUpdateMixin, CreateMixin):
    pass


class Update(AccountMixin, AjaxCreateUpdateMixin, UpdateMixin):
    pass


def load_to_account(request):
    id = request.GET.get('id')
    objects = Account.objects.exclude(pk=id)
    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
