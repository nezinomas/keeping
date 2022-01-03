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

    # @timer
    def get(self, request, *args, **kwargs):
        journal = request.user.journal
        dummy = SimpleNamespace()

        _years = years()

        # clean balance tables
        AccountBalance.objects.filter(account__journal=journal).delete()
        SavingBalance.objects.filter(saving_type__journal=journal).delete()
        PensionBalance.objects.filter(pension_type__journal=journal).delete()

        for year in _years:
            _pensions = pensions(year)
            _accounts = accounts(year)
            _savings = savings(year)

            if year > datetime.now().year:
                continue

            SignalBase.accounts(
                sender=dummy,
                instance=dummy,
                year=year,
                types=_accounts
            )
            SignalBase.savings(
                sender=dummy,
                instance=dummy,
                year=year,
                types=_savings
            )
            SignalBase.pensions(
                sender=dummy,
                instance=dummy,
                year=year,
                types=_pensions
            )

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

        SignalBase.accounts(
            sender=dummy,
            instance=dummy,
            year=year,
            types=accounts(year)
        )
        SignalBase.savings(
            sender=dummy,
            instance=dummy,
            year=year,
            types=savings(year)
        )
        SignalBase.pensions(
            sender=dummy,
            instance=dummy,
            year=year,
            types=pensions(year)
        )

        return JsonResponse({'redirect': self.redirect_view})


def accounts(year):
    qs = (
        Account
        .objects
        .items(year)
        .filter(created__year__lte=year)
        .values('id', 'title')
    )
    return _make_arr(qs)


def savings(year):
    qs = (
        SavingType
        .objects
        .related()
        .filter(
            Q(closed__isnull=True) | Q(closed__gt=year))
        .filter(created__year__lte=year)
        .values('id', 'title')
    )
    return _make_arr(qs)


def pensions(year):
    qs = (
        PensionType
        .objects
        .items()
        .filter(created__year__lte=year)
        .values('id', 'title')
    )
    return _make_arr(qs)


def _make_arr(qs):
    rtn = {}

    for x in qs:
        rtn[x['title']] = x['id']

    return rtn
