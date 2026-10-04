import itertools
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import NamedTuple

import polars as pl
from django.utils.translation import gettext as _

from ...pensions.services.model_services import PensionBalanceModelService
from ...savings.models import SavingBalance
from ...savings.services.model_services import SavingBalanceModelService
from ...transactions.services.model_services import SavingChangeModelService

NO_SWITCHES = MappingProxyType({})
# pensions II are a separate model with no switches
SWITCHABLE = {"funds", "shares", "pensions"}


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

    def process_data(self, data, switched: Mapping[int, int]):
        df = pl.DataFrame(data)
        if df.is_empty():
            return

        df = self._process_dataframe(df, switched)
        self._update_attributes(df)

    def _process_dataframe(self, df, switched: Mapping[int, int]):
        base = pl.col.incomes - pl.col.year.replace_strict(switched, default=0)
        return (
            df.lazy()
            .group_by(pl.col.year)
            .agg([pl.col.incomes.sum(), pl.col.profit.sum(), pl.col.total.sum()])
            .with_columns((pl.col.total - pl.col.profit).alias("invested"))
            .filter(pl.col.year <= datetime.now().year)
            .filter((pl.col.total != 0) | (pl.col.profit != 0))
            .with_columns(
                proc=pl.when(base > 0)
                .then((pl.col.profit * 100) / base)
                .otherwise(0.0)
                .round(1)
            )
            .sort(pl.col.year)
        ).collect()

    def _update_attributes(self, df):
        self.categories = df["year"].to_list()
        self.invested = df["invested"].to_list()
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

    @property
    def pointer(self) -> str:
        return "_".join(self.keys)


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


def get_data(user, saving_types: list = None):
    if saving_types is None:
        saving_types = ["funds", "shares", "pensions"]

    data = {
        saving_type: list(
            SavingBalanceModelService(user).sum_by_type().filter(type=saving_type)
        )
        for saving_type in saving_types
    }
    data["pensions2"] = list(PensionBalanceModelService(user).sum_by_year())

    return data


def hidden_by_year(user) -> dict[int, frozenset[int]]:
    """Per year, the funds whose row shows no profit."""
    rows = (
        SavingBalanceModelService(user)
        .objects.exclude(SavingBalance.shows_profit_q())
        .values_list("year", "saving_type_id")
    )
    hidden = defaultdict(set)
    for year, fund in rows:
        hidden[year].add(fund)
    return {year: frozenset(funds) for year, funds in hidden.items()}


def switched_by_group(user, data: dict) -> dict[str, dict[int, int]]:
    """Per chart pointer and year, the money switched within the group's types,
    which the % takes off its base as the funds table does."""
    service = SavingChangeModelService(user)
    hidden = hidden_by_year(user)
    switched = {}
    for chart_keys in chart_keys_map():
        if not set(chart_keys.keys) <= SWITCHABLE & data.keys():
            continue
        years = {row["year"] for key in chart_keys.keys for row in data[key]}
        switched[chart_keys.pointer] = service.switched_within_years(
            years, chart_keys.keys, hidden
        )
    return switched


def make_chart(title: str, *args, switched: Mapping[int, int] = NO_SWITCHES) -> dict:
    chart = Chart(title)
    data = itertools.chain.from_iterable(args)
    chart.process_data(data, switched)
    return asdict(chart)


def update_context(context, chart, chart_pointer):
    if records := len(chart["categories"]):
        context.add_chart(chart_pointer, chart, records)


def load_service(data, maps=None, switched: Mapping = NO_SWITCHES):
    context = Context()

    if not maps:
        maps = chart_keys_map()

    for i in maps:
        data_args = [data[x] for x in i.keys]
        chart = make_chart(
            i.title, *data_args, switched=switched.get(i.pointer, NO_SWITCHES)
        )
        update_context(context, chart, i.pointer)

    return asdict(context)


def load(user) -> dict:
    data = get_data(user)
    return load_service(data, switched=switched_by_group(user, data))
