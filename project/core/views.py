from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from ..accounts.models import Account
from ..core.signals import SignalBase
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .lib.date import years
from .mixins.views import DispatchAjaxMixin
from .tests.utils import timer


@login_required()
def set_year(request, year):
    if year in years():
        user = request.user
        user.year = year
        user.save()

    url = request.META.get('HTTP_REFERER', '/')

    return redirect(url)


@login_required
def set_month(request, month):
    if month in range(1, 13):
        user = request.user
        user.month = month
        user.save()

    url = request.META.get('HTTP_REFERER', '/')

    return redirect(url)


class RegenerateBalances(LoginRequiredMixin, DispatchAjaxMixin, View):
    redirect_view = reverse_lazy('bookkeeping:index')

    @timer
    def get(self, request, *args, **kwargs):
        _years = years()

        dummy = SimpleNamespace()

        _accounts = accounts()
        _savings = savings()
        _pensions = pensions()

        for year in _years:
            SignalBase.accounts(dummy, dummy, year, _accounts)
            SignalBase.savings(dummy, dummy, year, _savings)
            SignalBase.pensions(dummy, dummy, year, _pensions)

        return JsonResponse({'redirect': self.redirect_view})


class RegenerateBalancesCurrentYear(LoginRequiredMixin, DispatchAjaxMixin, View):
    redirect_view = reverse_lazy('bookkeeping:index')

    @timer
    def get(self, request, *args, **kwargs):
        year = request.user.year
        dummy = SimpleNamespace()

        SignalBase.accounts(dummy, dummy, year, accounts())
        SignalBase.savings(dummy, dummy, year, savings())
        SignalBase.pensions(dummy, dummy, year, pensions())

        return JsonResponse({'redirect': self.redirect_view})


def accounts():
    qs = Account.objects.items().values('id', 'title')
    return {x['title']: x['id'] for x in qs}


def savings():
    qs = SavingType.objects.items().values('id', 'title')
    return {x['title']: x['id'] for x in qs}


def pensions():
    qs = PensionType.objects.items().values('id', 'title')
    return {x['title']: x['id'] for x in qs}
