from datetime import datetime

from django.template.loader import render_to_string

from .. import models
from .drinks_stats import DrinkStats, std_av


def context_to_reload(request, context):
    year = request.user.year

    qs_target = models.DrinkTarget.objects.year(year)
    qs_drinks = models.Drink.objects.sum_by_month(year)
    qs_drinks_days = models.Drink.objects.day_sum(year)

    _DrinkStats = DrinkStats(qs_drinks)
    print(_DrinkStats.consumption)
    # values
    avg = qs_drinks_days.get('per_day', 0) if qs_drinks_days else 0
    qty = qs_drinks_days.get('qty', 0) if qs_drinks_days else 0
    target = qs_target[0].quantity if qs_target else 0

    context['chart_quantity'] = render_to_string(
        'drinks/includes/chart_quantity_per_month.html',
        {'data': _DrinkStats.quantity},
        request
    )

    context['chart_consumsion'] = render_to_string(
        'drinks/includes/chart_consumsion_per_month.html', {
            'data': _DrinkStats.consumption,
            'target': target,
            'avg': avg,
            'avg_label_y': _avg_label_position(avg, target),
            'target_label_y': _target_label_position(avg, target),
        },
        request
    )

    context['tbl_consumsion'] = render_to_string(
        'drinks/includes/tbl_consumsion.html',
        {'qty': qty, 'avg': avg, 'target': target},
        request)

    context['tbl_last_day'] = render_to_string(
        'drinks/includes/tbl_last_day.html',
        _dry_days(year),
        request=request
    )

    context['tbl_alcohol'] = render_to_string(
        'drinks/includes/tbl_alcohol.html',
        {'l': qty * 0.025},
        request
    )

    context['tbl_std_av'] = render_to_string(
        'drinks/includes/tbl_std_av.html',
        {'items': std_av(year, qty)},
        request
    )


def _avg_label_position(avg, target):
    return 15 if target - 50 <= avg <= target else -5


def _target_label_position(avg, target):
    return 15 if avg - 50 <= target <= avg else -5


def _dry_days(year):
    qs = None
    try:
        qs = models.Drink.objects.year(year).latest()
    except models.Drink.DoesNotExist:
        pass

    if qs:
        latest = qs.date
        delta = (datetime.now().date() - latest).days
        return {'date': latest, 'delta': delta}

    return {}
