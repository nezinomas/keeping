import contextlib
import itertools
from dataclasses import dataclass, field
from datetime import datetime

from django.utils.translation import gettext as _

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class SummarySavingsServiceData:
    funds: list = field(init=False, default_factory=list)
    shares: list = field(init=False, default_factory=list)
    pensions2: list = field(init=False, default_factory=list)
    pensions3: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.funds = list(SavingBalance.objects.sum_by_type().filter(type="funds"))
        self.shares = list(SavingBalance.objects.sum_by_type().filter(type="shares"))
        self.pensions2 = list(PensionBalance.objects.sum_by_year())
        self.pensions3 = list(
            SavingBalance.objects.sum_by_type().filter(type="pensions")
        )


class SummarySavingsService:
    def __init__(self, data: SummarySavingsServiceData):
        self.funds = data.funds
        self.shares = data.shares
        self.pensions2 = data.pensions2
        self.pensions3 = data.pensions3

    @property
    def records(self):
        return (
            0
            + len(self.funds)
            + len(self.shares)
            + len(self.pensions2)
            + len(self.pensions3)
        )

    def make_chart_data(self, *attr_names: str) -> list[dict]:
        """
        attr_names
        available: funds, shares, pensions2, pensions3
        """
        data = []

        for attr in attr_names:
            with contextlib.suppress(AttributeError):
                data.append(getattr(self, attr))

        return __class__.chart_data(*data)

    @staticmethod
    def chart_data(*args):
        items = {
            "text_total": _("Total"),
            "text_profit": _("Profit"),
            "text_invested": _("Invested"),
            "categories": [],
            "invested": [],
            "profit": [],
            "total": [],
            "max": 0,
        }

        # from tuple[list[dict]] make list[dict]
        data = itertools.chain.from_iterable(args)

        for row in data:
            _year = row.get("year")
            _invested = row.get("invested")
            _profit = row.get("profit")
            _total_sum = _invested + _profit

            if _year > datetime.now().year:
                continue

            if not _invested and not _profit:
                continue

            if _year not in items["categories"]:
                items["categories"].append(_year)
                items["invested"].append(_invested)
                items["profit"].append(_profit)
                items["total"].append(_total_sum)
            else:
                ix = items["categories"].index(_year)  # category index
                items["invested"][ix] += _invested
                items["profit"][ix] += _profit
                items["total"][ix] += _total_sum

        # max value
        with contextlib.suppress(ValueError):
            items["max"] = max(items.get("profit")) + max(items.get("invested"))

        return items
