from typing import Dict, List

from crequest.middleware import CrequestMiddleware
from django.apps import apps

from ...accounts.models import Account, AccountBalance
from ...bookkeeping.lib.account_stats import AccountStats
from ...bookkeeping.lib.summary import collect_summary_data


def post_save_account_stats(account_id: int):
    request = CrequestMiddleware.get_request()
    year = request.user.profile.year

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


def _account_worth() -> List[Dict]:
    model = apps.get_model('bookkeeping.AccountWorth')
    return model.objects.items()


def _accounts(account_id: int = None) -> Dict[str, int]:
    qs = Account.objects.items()

    if account_id:
        qs = qs.filter(id=account_id)

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
