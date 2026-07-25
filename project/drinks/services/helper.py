from .. import models
from ..lib.drinks_stats import DrinkStats
from .consumption_year import ConsumptionYear


def drink_type_dropdown(request):
    drink_type = request.user.drink_type

    return {
        "select_drink_type": zip(models.DrinkType.labels, models.DrinkType.values),
        "current_drink_type": models.DrinkType(drink_type).label,
    }


def several_years_consumption(user, years):
    series = []

    for year in years:
        records = ConsumptionYear(user, int(year))
        if not records.monthly:
            continue

        stats = DrinkStats(records.converter, records.monthly)
        series.append({"name": year, "data": stats.monthly.avg_daily_volume_ml})

    return series
