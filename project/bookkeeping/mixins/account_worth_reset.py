from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils import timezone

from ...accounts.models import Account
from ...core.mixins.views import httpHtmxResponse, TemplateView
from ..models import AccountWorth


class AccountWorthResetMixin(TemplateView):
    account = None

    def get_object(self):
        account = None
        try:
            account = \
                Account.objects \
                .related() \
                .get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            pass

        return account

    def dispatch(self, request, *args, **kwargs):
        self.account = self.get_object()
        worth = None

        if self.account:
            try:
                worth = \
                    AccountWorth.objects \
                    .filter(account=self.account) \
                    .latest('date')
            except ObjectDoesNotExist:
                pass

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
