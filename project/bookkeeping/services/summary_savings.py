import contextlib
import itertools
from typing import NamedTuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

from django.utils.translation import gettext as _

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


def get_data():
    types = ["funds", "shares", "pensions"]
    data = {}
    for t in types:
        data[t] = list(SavingBalance.objects.sum_by_type().filter(type=t))
    data["pensions2"] = list(PensionBalance.objects.sum_by_year())
    return data


def make_chart_data(*args):
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


def process_chart(i, data):
    chart_pointer = ("_").join(i.keys)
    chart_data = make_chart_data(*[data[x] for x in i.keys])
    chart_data["chart_title"] = i.title
    records = len(chart_data["categories"])
    return chart_pointer, chart_data, records


def load_service(data):
    context = Context()

    for i in chart_titles:
        chart_pointer, chart_data, records = process_chart(i, data)
        if records:
            context.add_chart(chart_pointer, chart_data, records)

    return asdict(context)
