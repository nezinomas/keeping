from django.db.models import Q

# A stale worth counts as 0 until a worth dated after the move is entered.
FRESH_WORTH = Q(sold_since_check=0)


class ShowsProfitMixin:
    """A balance row shows a profit unless its worth is stale or missing."""

    fund_field: str

    @property
    def shows_profit(self) -> bool:
        fund = getattr(self, self.fund_field)
        in_close_year = fund.closed == self.year and self.sold != 0
        fresh_worth = self.market_value != 0 and self.sold_since_check == 0
        return fresh_worth or in_close_year
