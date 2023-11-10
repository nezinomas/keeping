import itertools
import polars as pl

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
        df = pl.DataFrame(data)
        if df.is_empty():
            return

        df = (
            df.lazy()
            .group_by(pl.col.year)
            .agg(
                [pl.col.invested.sum(), pl.col.profit.sum()]
            )
            .with_columns(
                (pl.col.invested + pl.col.profit).alias("total"),
                (pl.col.invested.abs() + pl.col.profit.abs()).alias("max_value"),
            )
            .filter(pl.col.year <= datetime.now().year)
            .filter((pl.col.invested != 0.0) & (pl.col.profit != 0.0))
            .sort(pl.col.year)
        ).collect()

        self.categories = df["year"].to_list()
        self.invested = df["invested"].to_list()
        self.profit = df["profit"].to_list()
        self.total = df["total"].to_list()
        self.max_value = df["max_value"].max()


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


CHART_KEYS_MAP = [
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

    for i in CHART_KEYS_MAP:
        data_args = [data[x] for x in i.keys]
        chart = make_chart(i.title, *data_args)

        if records := len(chart["categories"]):
            chart_pointer = ("_").join(i.keys)
            context.add_chart(chart_pointer, chart, records)

    return asdict(context)
