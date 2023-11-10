import contextlib
import itertools
from typing import NamedTuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

from django.utils.translation import gettext as _

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class Chart:
    title: str
    text_total: str = field(init=False, default=_("Total"))
    text_profit: str = field(init=False, default=_("Profit"))
    text_invested: str = field(init=False, default=_("Invested"))
    categories: list = field(init=False, default_factory=list)
    invested: list = field(init=False, default_factory=list)
    profit: list = field(init=False, default_factory=list)
    total: list = field(init=False, default_factory=list)
    max_value: int = field(init=False, default=0)

    def process_data(self, data):
        for row in data:
            year = row.get("year")
            invested = row.get("invested")
            profit = row.get("profit")
            total_sum = invested + profit

            if year > datetime.now().year:
                continue

            if not invested and not profit:
                continue

            ix = self.categories.index(year) if year in self.categories else None
            if ix is None:
                self._add(year, invested, profit, total_sum)
            else:
                self._update(ix, invested, profit, total_sum)

        self._calculate_max()

    def _add(self, year, invested, profit, total_sum):
        self.categories.append(year)
        self.invested.append(invested)
        self.profit.append(profit)
        self.total.append(total_sum)

    def _update(self, ix, invested, profit, total_sum):
        self.invested[ix] += invested
        self.profit[ix] += profit
        self.total[ix] += total_sum

    def _calculate_max(self):
        with contextlib.suppress(ValueError):
            self.max_value = max(self.profit) + max(self.invested)


@dataclass
class Context:
    records: int = field(default=0, init=False)
    charts: dict = field(default_factory=dict, init=False)
    pointers: list = field(default_factory=list, init=False)

    def add_chart(self, pointer, data, records):
        self.charts[pointer] = data
        self.records += records
        self.pointers.append(pointer)


class ChartKeys(NamedTuple):
    title: str
    keys: list


CHARTS_MAP = [
    ChartKeys(_("Funds"), ["funds"]),
    ChartKeys(_("Shares"), ["shares"]),
    ChartKeys(f"{_('Funds')}, {_('Shares')}", ["funds", "shares"]),
    ChartKeys(f"{_('Pensions')} III", ["pensions"]),
    ChartKeys(f"{_('Pensions')} II", ["pensions2"]),
    ChartKeys(
        f"{_('Funds')}, {_('Shares')}, {_('Pensions')}",
        ["funds", "shares", "pensions"],
    ),
]


def get_data(saving_type: list = None):
    if saving_type is None:
        saving_type = ["funds", "shares", "pensions"]

    data = {
        t: list(SavingBalance.objects.sum_by_type().filter(type=t)) for t in saving_type
    }
    data["pensions2"] = list(PensionBalance.objects.sum_by_year())

    return data


def make_chart(title: str, *args) -> dict:
    chart = Chart(title)
    data = itertools.chain.from_iterable(args)
    chart.process_data(data)
    return asdict(chart)


def load_service(data):
    context = Context()

    for i in CHARTS_MAP:
        data_args = [data[x] for x in i.keys]
        chart = make_chart(i.title, *data_args)

        if records := len(chart["categories"]):
            chart_pointer = ("_").join(i.keys)
            context.add_chart(chart_pointer, chart, records)

    return asdict(context)
