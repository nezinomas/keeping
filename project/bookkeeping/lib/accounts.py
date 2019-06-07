from ...accounts.models import Account


class Accounts(object):
    def __init__(self):
        self._accounts = self._get_accounts()

    @property
    def accounts_list(self):
        return self._accounts

    @property
    def accounts_dictionary(self):
        items = {}
        for account in self._accounts:
            items[account] = 0

        return items

    def _get_accounts(self):
        qs = Account.objects.values_list('title', flat=True)
        return list(qs)
