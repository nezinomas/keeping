import contextlib
import itertools
from typing import NamedTuple
from datetime import datetime

from django.utils.translation import gettext as _

from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


def get_data():
    return {
        "funds": list(SavingBalance.objects.sum_by_type().filter(type="funds")),
        "shares": list(SavingBalance.objects.sum_by_type().filter(type="shares")),
        "pensions2": list(PensionBalance.objects.sum_by_year()),
        "pensions3": list(SavingBalance.objects.sum_by_type().filter(type="pensions")),
    }


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


class ChartKeys(NamedTuple):
    title: str
    keys: list


chart_titles = [
    ChartKeys(_("Funds"), ["funds"]),
    ChartKeys(_("Shares"), ["shares"]),
    ChartKeys(f"{_('Funds')}, {_('Shares')}", ["funds", "shares"]),
    ChartKeys(f"{_('Pensions')} III", ["pensions3"]),
    ChartKeys(f"{_('Pensions')} II", ["pensions2"]),
    ChartKeys(
        f"{_('Funds')}, {_('Shares')}, {_('Pensions')}",
        ["funds", "shares", "pensions3"],
    ),
]


def load_service(data):
    context = {"records": 0, "charts": []}
    charts = {}

    for i in chart_titles:
        template_var = ("_").join(i.keys)

        chart_data = make_chart_data(*[data[x] for x in i.keys])
        chart_data["chart_title"] = i.title

        records = len(chart_data["categories"])
        if not records:
            continue

        charts[template_var] = chart_data

        # update context
        context["records"] += records
        context["charts"].append(template_var)

    return context | charts
