import itertools
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import NamedTuple

import polars as pl
from django.utils.translation import gettext as _

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class Chart:
    title: str

    text_total: str = field(init=False)
    text_profit: str = field(init=False)
    text_invested: str = field(init=False)

    categories: list = field(init=False, default_factory=list)
    invested: list = field(init=False, default_factory=list)
    profit: list = field(init=False, default_factory=list)
    total: list = field(init=False, default_factory=list)
    proc: float = field(init=False, default=0.0)

    def __post_init__(self):
        self.text_total = _("Total")
        self.text_profit = _("Profit")
        self.text_invested = _("Invested")

    def process_data(self, data):
        df = pl.DataFrame(data)
        if df.is_empty():
            return

        df = self._process_dataframe(df)
        self._update_attributes(df)

    def _process_dataframe(self, df):
        return (
            df
            .lazy()
            .group_by(pl.col.year)
            .agg(
                [pl.col.incomes.sum(), pl.col.profit.sum()]
            )
            .with_columns(
                (pl.col.incomes + pl.col.profit).alias("total"),
            )
            .filter(pl.col.year <= datetime.now().year)
            .filter((pl.col.incomes != 0.0) & (pl.col.profit != 0.0))
            .with_columns(proc=((pl.col.profit * 100) / pl.col.incomes).round(1))
            .sort(pl.col.year)
        ).collect()

    def _update_attributes(self, df):
        self.categories = df["year"].to_list()
        self.invested = df["incomes"].to_list()
        self.profit = df["profit"].to_list()
        self.total = df["total"].to_list()
        self.proc = df["proc"].to_list()


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


def chart_keys_map():
    return [
        ChartKeys(_("Funds"), ["funds"]),
        ChartKeys(_("Shares"), ["shares"]),
        ChartKeys(f"{_('Funds')}, {_('Shares')}", ["funds", "shares"]),
        ChartKeys(f"{_('Pensions')} III", ["pensions"]),
        ChartKeys(f"{_('Pensions')} II", ["pensions2"]),
        ChartKeys(
            f"{_('Funds')}, {_('Shares')}, {_('Pensions')} III",
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


def update_context(context, chart, chart_pointer):
    if records := len(chart["categories"]):
        context.add_chart(chart_pointer, chart, records)


def load_service(data, maps=None):
    context = Context()

    if not maps:
        maps = chart_keys_map()

    for i in maps:
        data_args = [data[x] for x in i.keys]
        chart = make_chart(i.title, *data_args)
        chart_pointer = ("_").join(i.keys)
        update_context(context, chart, chart_pointer)

    return asdict(context)
