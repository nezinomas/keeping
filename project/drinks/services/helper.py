from .. import models
from ..lib.drinks_stats import DrinksOptions, DrinkStats
from ..services.model_services import DrinkModelService


def drink_type_dropdown(request):
    drink_type = request.user.drink_type

    return {
        "select_drink_type": zip(models.DrinkType.labels, models.DrinkType.values),
        "current_drink_type": models.DrinkType(drink_type).label,
    }


def several_years_consumption(user, years):
    serries = []
    for y in years:
        qs_drinks = DrinkModelService(user).sum_by_month(int(y))
        if not qs_drinks.exists():
            continue

        options = DrinksOptions(user.drink_type)
        data = DrinkStats(options, qs_drinks).per_day_of_month

        serries.append({"name": y, "data": data})

    return serries
