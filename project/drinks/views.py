from django.template.loader import render_to_string

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.drinks_stats import DrinkStats


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        qs_target = models.DrinkTarget.objects.year(year)
        qs_drinks = models.Drink.objects.month_sum(year)
        qs_drinks_days = models.Drink.objects.day_sum(year)

        _DrinkStats = DrinkStats(qs_drinks)

        # values
        avg_val = qs_drinks_days.get('per_day', 0)
        target_val = qs_target[0].quantity

        # calculate target and average label postions
        avg_label_y_position = -5
        target_label_y_position = -5

        if avg_val >= target_val - 25 and avg_val <= target_val:
            avg_label_y_position = 15

        if target_val >= avg_val - 25 and target_val <= avg_val:
            target_label_y_position = 15

        context['drinks_list'] = Lists.as_view()(
            self.request, as_string=True)
        context['target_list'] = render_to_string(
            'drinks/includes/drinks_target_list.html',
            {'items': qs_target},
            self.request)

        context['chart_consumsion'] = _DrinkStats.consumsion
        context['target'] = target_val
        context['avg'] = avg_val
        context['avg_label_y_position'] = avg_label_y_position
        context['target_label_y_position'] = target_label_y_position

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
