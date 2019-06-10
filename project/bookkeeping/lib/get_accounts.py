from ...accounts.models import Account


class GetData(object):
    def __init__(self):
        self._accounts = self._get_data()

    @property
    def accounts(self):
        return self._accounts

    def _get_data(self):
        qs = Account.objects.values_list('title', flat=True)

        items = {}
        for account in qs:
            items[account] = 0

        return items
