from datetime import datetime

from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.drinks_stats import DrinkStats


def _index(request, context):
    year = request.user.profile.year
    qs_target = models.DrinkTarget.objects.year(year)
    qs_drinks = models.Drink.objects.month_sum(year)
    qs_drinks_days = models.Drink.objects.day_sum(year)

    _DrinkStats = DrinkStats(qs_drinks)

    # values
    avg_val = qs_drinks_days.get('per_day', 0)
    qty_val = qs_drinks_days.get('qty', 0)
    target_val = qs_target[0].quantity

    # calculate target and average label postions
    avg_label_y_position = -5
    target_label_y_position = -5

    if avg_val >= target_val - 25 and avg_val <= target_val:
        avg_label_y_position = 15

    if target_val >= avg_val - 25 and target_val <= avg_val:
        target_label_y_position = 15

    context['drinks_list'] = Lists.as_view()(
        request, as_string=True)
    context['target_list'] = render_to_string(
        'drinks/includes/drinks_target_list.html',
        {'items': qs_target},
        request)

    context['target'] = target_val
    context['avg'] = avg_val

    context['chart_quantity'] = render_to_string(
        'drinks/includes/chart_quantity_per_month.html',
        {'data': _DrinkStats.quantity},
        request
    )

    context['chart_consumsion'] = render_to_string(
        'drinks/includes/chart_consumsion_per_month.html', {
            'data': _DrinkStats.consumsion,
            'target': target_val,
            'avg': avg_val,
            'avg_label_y_position': avg_label_y_position,
            'target_label_y_position': target_label_y_position,
        },
        request
    )

    context['tbl_consumsion'] = render_to_string(
        'drinks/includes/tbl_consumsion.html',
        {'qty': qty_val, 'avg': avg_val},
        request)

    qs_last = models.Drink.objects.latest()

    context['tbl_last_day'] = render_to_string(
        'drinks/includes/tbl_last_day.html', {
            'date': qs_last.date,
            'delta': (datetime.now().date() - qs_last.date).days
        },
        request
    )

    context['tbl_alcohol'] = render_to_string(
        'drinks/includes/tbl_alcohol.html',
        {'l': qty_val * 0.025},
        request
    )


def reload_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    context = {}
    t_name = 'drinks/includes/reload_stats.html'

    _index(request, context)

    if ajax_trigger:
        return render(template_name=t_name, context=context, request=request)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _index(self.request, context)

        return context


class Lists(ListMixin):
    model = models.Drink


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class TargetLists(ListMixin):
    model = models.DrinkTarget


class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
