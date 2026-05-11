from .. import models
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DrinkStats
from ..services.model_services import DrinkModelService


def drink_type_dropdown(request):
    drink_type = request.user.drink_type

    return {
        "select_drink_type": zip(models.DrinkType.labels, models.DrinkType.values),
        "current_drink_type": models.DrinkType(drink_type).label,
    }


def several_years_consumption(user, years):
    series = []
    converter = DrinkConverter(user.drink_type)

    for year in years:
        drinks_data = DrinkModelService(user).sum_by_month(int(year))
        if not drinks_data.exists():
            continue

        monthly_averages = DrinkStats(converter, drinks_data).monthly.avg_daily_volume_ml
        series.append({"name": year, "data": monthly_averages})

    return series
