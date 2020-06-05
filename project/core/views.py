from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse

from ..core.signals import (post_save_account_stats, post_save_pension_stats,
                            post_save_saving_stats)
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
    months = range(1, 13)
    if month not in months:
        month = 1

    user = request.user
    user.month = month
    user.save()

    url = request.META.get('HTTP_REFERER', '/')

    return redirect(url)


@login_required
def index(request):
    return render(request, 'core/index.html')


@login_required
def regenerate_balances(request):
    _years = years()

    for year in _years:
        post_save_account_stats(SimpleNamespace(), year)
        post_save_saving_stats(SimpleNamespace(), year)
        post_save_pension_stats(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )


@login_required
def regenerate_balances_current_year(request, year):
    post_save_account_stats(SimpleNamespace(), year)
    post_save_saving_stats(SimpleNamespace(), year)
    post_save_pension_stats(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )
