from django.db.models import F, Q

# A stale worth counts as 0 until a worth dated after the move is entered.
FRESH_WORTH = Q(sold_since_check=0)


class ShowsProfitMixin:
    """A balance row shows a profit unless its worth is stale or missing.

    Its model names the row's Fund in `fund`, and that Fund's closing year as a
    lookup in `fund_closed_lookup`."""

    fund_closed_lookup: str

    @property
    def shows_profit(self) -> bool:
        in_close_year = self.fund.closed == self.year and self.sold != 0
        fresh_worth = self.market_value != 0 and self.sold_since_check == 0
        return fresh_worth or in_close_year

    @classmethod
    def shows_profit_q(cls) -> Q:
        """The rows `shows_profit` is true for, for the aggregated querysets."""
        in_close_year = Q(**{cls.fund_closed_lookup: F("year")}) & ~Q(sold=0)
        return (~Q(market_value=0) & FRESH_WORTH) | in_close_year
