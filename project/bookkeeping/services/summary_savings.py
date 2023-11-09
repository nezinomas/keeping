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


class ChartKeys(NamedTuple):
    title: str
    keys: list


@dataclass
class Context:
    records: int = field(default=0, init=False)
    charts: dict = field(default_factory=dict, init=False)
    pointers: list = field(default_factory=list, init=False)

    def add_chart(self, pointer, data, records):
        self.charts[pointer] = data
        self.records += records
        self.pointers.append(pointer)


def get_data():
    types = ["funds", "shares", "pensions"]
    data = {}
    for t in types:
        data[t] = list(SavingBalance.objects.sum_by_type().filter(type=t))
    data["pensions2"] = list(PensionBalance.objects.sum_by_year())
    return data


def make_chart(title: str, *args) -> dict:
    chart = Chart(title)
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

        _update_chart(chart, _year, _invested, _profit, _total_sum)

    # max value
    with contextlib.suppress(ValueError):
        chart.max_value = max(chart.profit) + max(chart.invested)

    return asdict(chart)


def _update_chart(chart, year, invested, profit, total_sum):
    if year not in chart.categories:
        chart.categories.append(year)
        chart.invested.append(invested)
        chart.profit.append(profit)
        chart.total.append(total_sum)
    else:
        ix = chart.categories.index(year)  # category index
        chart.invested[ix] += invested
        chart.profit[ix] += profit
        chart.total[ix] += total_sum


chart_titles = [
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


def load_service(data):
    context = Context()

    for i in chart_titles:
        chart_pointer = ("_").join(i.keys)
        chart = make_chart(i.title, *[data[x] for x in i.keys])

        if records := len(chart["categories"]):
            context.add_chart(chart_pointer, chart, records)

    return asdict(context)
