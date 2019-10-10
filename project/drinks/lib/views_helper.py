from datetime import datetime

from django.template.loader import render_to_string

from .. import models
from .drinks_stats import DrinkStats, std_av


def context_to_reload(request, context):
    year = request.user.profile.year

    qs_target = models.DrinkTarget.objects.year(year)
    qs_drinks = models.Drink.objects.month_sum(year)
    qs_drinks_days = models.Drink.objects.day_sum(year)
    qs_last = models.Drink.objects.latest()

    _DrinkStats = DrinkStats(qs_drinks)

    # values
    avg = qs_drinks_days.get('per_day', 0)
    qty = qs_drinks_days.get('qty', 0)
    target_val = qs_target[0].quantity

    context['chart_quantity'] = render_to_string(
        'drinks/includes/chart_quantity_per_month.html',
        {'data': _DrinkStats.quantity},
        request
    )

    context['chart_consumsion'] = render_to_string(
        'drinks/includes/chart_consumsion_per_month.html', {
            'data': _DrinkStats.consumsion,
            'target': target_val,
            'avg': avg,
            'avg_label_y': _avg_label_position(avg, target_val),
            'target_label_y': _target_label_position(avg, target_val),
        },
        request
    )

    context['tbl_consumsion'] = render_to_string(
        'drinks/includes/tbl_consumsion.html',
        {'qty': qty, 'avg': avg, 'target': target_val},
        request)

    context['tbl_last_day'] = render_to_string(
        'drinks/includes/tbl_last_day.html', {
            'date': qs_last.date,
            'delta': (datetime.now().date() - qs_last.date).days
        },
        request
    )

    context['tbl_alcohol'] = render_to_string(
        'drinks/includes/tbl_alcohol.html',
        {'l': qty * 0.025},
        request
    )

    context['tbl_std_av'] = render_to_string(
        'drinks/includes/tbl_std_av.html',
        {'items': std_av(qty)},
        request
    )


def _avg_label_position(avg, target):
    y = -5

    if avg >= target - 50 and avg <= target:
        y = 15

    return y


def _target_label_position(avg, target):
    y = -5

    if target >= avg - 50 and target <= avg:
        y = 15

    return y
