from typing import Dict, List

from crequest.middleware import CrequestMiddleware
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..accounts.models import Account, AccountBalance
from ..bookkeeping.lib.account_stats import AccountStats
from ..bookkeeping.lib.summary import collect_summary_data
from ..incomes.models import Income
from ..savings.models import Saving


@receiver(post_save, sender=Income)
@receiver(post_save, sender=Saving)
def post_save_account_stats(instance, *args, **kwargs):
    request = CrequestMiddleware.get_request()
    year = request.user.profile.year

    account_id = _account_id(instance)

    stats = _account_stats(year, account_id)

    for row in stats:
        # get id
        id = row['id']

        # delete dictionary keys
        del row['id']
        del row['title']

        obj, created = AccountBalance.objects.update_or_create(
            year=year,
            account_id=id,
            defaults={k: v for k, v in row.items()}
        )


def _account_id(instance: object) -> List[int]:
    account_id = []
    arr = ['account_id', 'from_account_id', 'to_account_id']
    for name in arr:
        id = getattr(instance, name, None)
        if id:
            account_id.append(id)

    return account_id


def _account_worth() -> List[Dict]:
    model = apps.get_model('bookkeeping.AccountWorth')
    return model.objects.items()


def _accounts(account_id: List[int] = None) -> Dict[str, int]:
    qs = Account.objects.items()

    if account_id:
        qs = qs.filter(id__in=account_id)

    qs = qs.values('id', 'title')

    return {x['title']: x['id'] for x in qs}


def _account_stats(year: int, account_id: int) -> List[Dict]:
    account_worth = _account_worth()
    account = _accounts(account_id)

    data = collect_summary_data(
        year=year,
        types=account,
        where='accounts'
    )

    return AccountStats(data, account_worth).balance
