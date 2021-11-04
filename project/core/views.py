from datetime import datetime
from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from ..accounts.models import Account, AccountBalance
from ..core.signals import SignalBase
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import SavingBalance, SavingType
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
        journal = request.user.journal
        _years = years()
        _pensions = pensions()
        dummy = SimpleNamespace()

        # clean balance tables
        AccountBalance.objects.filter(account__journal=journal).delete()
        SavingBalance.objects.filter(saving_type__journal=journal).delete()
        PensionBalance.objects.filter(pension_type__journal=journal).delete()

        for year in _years:
            if year > datetime.now().year:
                continue

            _accounts = accounts(year)
            _savings = savings(year)

            SignalBase.accounts(dummy, dummy, year, _accounts)
            SignalBase.savings(dummy, dummy, year, _savings)
            SignalBase.pensions(dummy, dummy, year, _pensions)

        return JsonResponse({'redirect': self.redirect_view})


class RegenerateBalancesCurrentYear(LoginRequiredMixin, DispatchAjaxMixin, View):
    redirect_view = reverse_lazy('bookkeeping:index')

    # @timer
    def get(self, request, *args, **kwargs):
        year = request.user.year
        journal = request.user.journal
        dummy = SimpleNamespace()

        # clean balance tables
        AccountBalance.objects.filter(account__journal=journal, year=year).delete()
        SavingBalance.objects.filter(saving_type__journal=journal, year=year).delete()
        PensionBalance.objects.filter(pension_type__journal=journal, year=year).delete()

        SignalBase.accounts(dummy, dummy, year, accounts(year))
        SignalBase.savings(dummy, dummy, year, savings(year))
        SignalBase.pensions(dummy, dummy, year, pensions())

        return JsonResponse({'redirect': self.redirect_view})


def accounts(year):
    qs = Account.objects.items(year=year).values('id', 'title')
    return {x['title']: x['id'] for x in qs}


def savings(year):
    qs = SavingType.objects.items(year=year).values('id', 'title')
    return {x['title']: x['id'] for x in qs}


def pensions():
    qs = PensionType.objects.items().values('id', 'title')
    return {x['title']: x['id'] for x in qs}
