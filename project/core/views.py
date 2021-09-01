from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import View

from ..core.signals import (accounts_post_signal, pensions_post_signal,
                            savings_post_signal)
from .lib.date import years
from .mixins.views import DispatchAjaxMixin


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

    def get(self, request, *args, **kwargs):
        _years = years()

        for year in _years:
            dummy = SimpleNamespace()

            accounts_post_signal(dummy, dummy, year)
            savings_post_signal(dummy, dummy, year)
            pensions_post_signal(dummy, dummy, year)

        return JsonResponse({'redirect': self.redirect_view})


class RegenerateBalancesCurrentYear(LoginRequiredMixin, DispatchAjaxMixin, View):
    redirect_view = reverse_lazy('bookkeeping:index')

    def get(self, request, *args, **kwargs):
        year = request.user.year
        dummy = SimpleNamespace()

        accounts_post_signal(dummy, dummy, year)
        savings_post_signal(dummy, dummy, year)
        pensions_post_signal(dummy, dummy, year)

        return JsonResponse({'redirect': self.redirect_view})
