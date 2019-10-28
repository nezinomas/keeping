from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse

from ..core.signals import post_save_account_stats, post_save_saving_stats
from .lib.date import years


@login_required()
def set_year(request, year, view_name):

    user = request.user
    user.profile.year = year
    user.save()

    return redirect(
        reverse(view_name, kwargs={}))


@login_required
def set_month(request, month, view_name):
    user = request.user
    user.profile.month = month
    user.save()

    return redirect(
        reverse(view_name, kwargs={}))


@login_required
def index(request):
    return render(request, 'core/index.html')


@login_required
def regenerate_balances(request):
    _years = years()

    for year in _years:
        post_save_account_stats(SimpleNamespace(), year)
        post_save_saving_stats(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )


@login_required
def regenerate_balances_current_year(request, year):
    post_save_account_stats(SimpleNamespace(), year)
    post_save_saving_stats(SimpleNamespace(), year)

    return redirect(
        reverse('bookkeeping:index', kwargs={})
    )
