import contextlib

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils import timezone

from ...accounts.models import Account
from ...core.mixins.views import TemplateView, httpHtmxResponse
from ..models import AccountWorth


class AccountWorthResetMixin(TemplateView):
    account = None

    def get_object(self):
        account = None
        with contextlib.suppress(ObjectDoesNotExist):
            account = \
                Account.objects \
                .related() \
                .get(pk=self.kwargs['pk'])

        return account

    def dispatch(self, request, *args, **kwargs):
        worth = None
        self.account = self.get_object()

        if self.account:
            with contextlib.suppress(ObjectDoesNotExist):
                worth = \
                    AccountWorth.objects \
                    .filter(account=self.account) \
                    .latest('date')
        worth_price = worth.price if worth else 0

        if not all((self.account, worth, worth_price)):
            return HttpResponse(status=204)  # 204 - No Content

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        AccountWorth.objects.create(
            price=0,
            account=self.account,
            date=timezone.now()
        )
        return httpHtmxResponse('afterReset')
