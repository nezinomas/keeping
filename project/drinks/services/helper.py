from .. import models
from ..lib.drinks_stats import DrinkStats


def drink_type_dropdown(request):
    drink_type = request.user.drink_type

    return {
        'select_drink_type': zip(models.DrinkType.labels, models.DrinkType.values),
        'current_drink_type': models.DrinkType(drink_type).label,
    }

def several_years_consumption(years):
    serries = []
    for y in years:
        qs_drinks = models.Drink.objects.sum_by_month(int(y))
        if not qs_drinks:
            continue

        data = DrinkStats(qs_drinks).per_day_of_month

        if not any(data):
            continue

        serries.append({'name': y, 'data': data})

    return serries
