from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, reverse

from ..core.signals import (accounts_post_signal, pensions_post_signal,
                            savings_post_signal)
from .lib.date import years


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


@login_required
def regenerate_balances(request):
    _years = years()

    for year in _years:
        accounts_post_signal(SimpleNamespace(), year)
        savings_post_signal(SimpleNamespace(), year)
        pensions_post_signal(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )


@login_required
def regenerate_balances_current_year(request, year):
    accounts_post_signal(SimpleNamespace(), year)
    savings_post_signal(SimpleNamespace(), year)
    pensions_post_signal(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )
