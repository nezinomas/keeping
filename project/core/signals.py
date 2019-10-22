from typing import Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..accounts.models import Account, AccountBalance
from ..bookkeeping.lib.account_stats import AccountStats
from ..bookkeeping.lib.summary import collect_summary_data
from ..bookkeeping.models import AccountWorth
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.models import Saving
from ..transactions.models import SavingChange, SavingClose, Transaction


@receiver(post_save, sender=Income)
def post_save_account_stats(sender, instance, *args, **kwargs):
    request = CrequestMiddleware.get_request()
    year = request.user.profile.year

    stats = _account_stats(year, instance.account.id)

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


def _account_worth() -> List[Dict]:
    return AccountWorth.objects.items()


def _accounts(account_id: int) -> Dict[str, int]:
    qs = (
        Account.objects.items()
        .filter(id=account_id)
        .values('id', 'title'))

    return {x['title']: x['id'] for x in qs}


def _account_stats(year: int, account_id: int) -> List[Dict]:
    account_worth = _account_worth()
    account = _accounts(account_id)

    data = collect_summary_data(
        year=year,
        types=account,
        models=[Income, Expense, Saving, SavingClose, Transaction]
    )

    return AccountStats(data, account_worth).balance
