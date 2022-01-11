from datetime import datetime
from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
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
        _years = years()

        for year in _years:
            _pensions = pensions(year)
            _accounts = accounts(year)
            _savings = savings(year)

            if year > datetime.now().year:
                continue

            SignalBase.accounts(
                sender=None,
                instance=None,
                year=year,
                all_id=_accounts
            )
            SignalBase.savings(
                sender=None,
                instance=None,
                year=year,
                all_id=_savings
            )
            SignalBase.pensions(
                sender=None,
                instance=None,
                year=year,
                all_id=_pensions
            )

        return JsonResponse({'redirect': self.redirect_view})


class RegenerateBalancesCurrentYear(LoginRequiredMixin, DispatchAjaxMixin, View):
    redirect_view = reverse_lazy('bookkeeping:index')

    @timer
    def get(self, request, *args, **kwargs):
        year = request.user.year

        SignalBase.accounts(
            sender=None,
            instance=None,
            year=year,
            all_id=accounts(year)
        )
        SignalBase.savings(
            sender=None,
            instance=None,
            year=year,
            all_id=savings(year)
        )
        SignalBase.pensions(
            sender=None,
            instance=None,
            year=year,
            all_id=pensions(year)
        )

        return JsonResponse({'redirect': self.redirect_view})


def accounts(year):
    qs = (
        AccountBalance
        .objects
        .related()
        .filter(year=year)
        .values_list('account_id', flat=True)
    )
    return list(qs)


def savings(year):
    qs = (
        SavingBalance
        .objects
        .related()
        .filter(year=year)
        .values_list('saving_type_id', flat=True)
    )
    return list(qs)


def pensions(year):
    qs = (
        PensionBalance
        .objects
        .related()
        .filter(year=year)
        .values_list('pension_type_id', flat=True)
    )
    return list(qs)
