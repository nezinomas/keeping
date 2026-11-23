from django.db.models import F, Q

from ..lib.money_cells import rounds_to_zero

# A stale worth counts as 0 until a worth dated after the move is entered.
FRESH_WORTH = Q(sold_since_check=0)


class ShowsProfitMixin:
    """A balance row shows a profit unless its worth is stale or missing.

    Its model returns the row's Owner, a Fund or a Pension fund, from `owner`, and
    names that Owner's closing year as a lookup in `owner_closed_lookup`."""

    owner_closed_lookup: str

    @property
    def owner(self):
        """The Owner whose `closed` year the row reads; its model returns it."""
        raise NotImplementedError

    @property
    def shows_profit(self) -> bool:
        in_close_year = self.owner.closed == self.year and self.sold != 0
        fresh_worth = self.market_value != 0 and self.sold_since_check == 0
        return fresh_worth or in_close_year

    @property
    def profit_proc_signed(self) -> bool:
        """The percent wears its sum's sign, unless it reads 0%."""
        return not rounds_to_zero(self.profit_proc)

    @classmethod
    def shows_profit_q(cls) -> Q:
        """The rows `shows_profit` is true for, for the aggregated querysets."""
        in_close_year = Q(**{cls.owner_closed_lookup: F("year")}) & ~Q(sold=0)
        return (~Q(market_value=0) & FRESH_WORTH) | in_close_year
