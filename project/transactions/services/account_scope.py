from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import pgettext

from ...accounts.models import Account
from ...accounts.services.model_services import AccountModelService
from ...core.lib.filter_line import FilterItem

OPEN = "open"
ALL = "all"


def closed_year_before(account: Account, year: int) -> int:
    # Account.closed stays None while the account is open (Avoid None 5)
    if account.closed is None or account.closed >= year:
        return 0
    return account.closed


@dataclass(frozen=True)
class AccountScope:
    value: str

    @classmethod
    def parse(cls, value: str) -> "AccountScope":
        if value in (OPEN, ALL):
            return cls(value)
        return cls(OPEN)

    def url(self) -> str:
        return reverse("transactions:tab_accounts", args=[self.value])

    def rows(
        self, service: AccountModelService, year: int
    ) -> list[tuple[Account, int]]:
        accounts = service.items_in(year)
        if self.value == ALL:
            accounts = service.all()
        pairs = [(account, closed_year_before(account, year)) for account in accounts]
        open_pairs = [pair for pair in pairs if not pair[1]]
        closed_pairs = [pair for pair in pairs if pair[1]]
        return open_pairs + sorted(
            closed_pairs, key=lambda pair: (pair[1], pair[0].title)
        )

    def items(self) -> list[FilterItem]:
        labels = {
            OPEN: pgettext("account scope", "Open"),
            ALL: pgettext("account scope", "All"),
        }
        return [
            FilterItem(label, AccountScope(value).url(), value == self.value)
            for value, label in labels.items()
        ]
