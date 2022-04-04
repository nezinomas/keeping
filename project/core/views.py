from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from ..core.signals_base import SignalBase
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
        _arr = []
        _type = request.GET.get('type')
        _kwargs = {
            'sender': None,
            'instance': None,
            'created': False,
            'signal': 'any',
            'update_on_load': False,
        }

        _types = ['accounts', 'savings', 'pensions']

        if _type and _type in _types:
            _types = [_type]

        for x in _types:
            _class_method = getattr(SignalBase, x)
            _obj = _class_method(**_kwargs)
            _obj.full_balance_update()

        return JsonResponse({'redirect': self.redirect_view})
