from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.date import years
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .apps import App_name
from .lib import views_helper as H


class ReloadStats(DispatchAjaxMixin, IndexMixin):
    template_name = f'{App_name}/includes/reload_stats.html'
    redirect_view = reverse_lazy(f'{App_name}:{App_name}_index')

    def get(self, request, *args, **kwargs):
        context = H.RenderContext(request).context_to_reload()
        return self.render_to_response(context)


class HistoricalData(IndexMixin):
    template_name = f'{App_name}/includes/chart_compare.html'

    def get(self, request, *args, **kwargs):
        year = request.user.year + 1
        qty = kwargs.get('qty', 0)
        chart_serries = H.several_years_consumption(range(year - qty, year))
        context = {
            'serries': chart_serries,
            'chart_container_name': 'history_chart',
        }
        rendered = render_to_string(self.template_name, context, request)

        return JsonResponse({'html': rendered})


class Compare(AjaxSearchMixin):
    template_name = f'{App_name}/includes/compare_form.html'
    form_class = forms.DrinkCompareForm
    form_data_dict = {}

    def form_valid(self, form, **kwargs):
        html = _('No data')
        years_data = [self.form_data_dict['year1'], self.form_data_dict['year2']]
        chart_serries = H.several_years_consumption(years_data)

        if len(chart_serries) == 2:
            template = f'{App_name}/includes/chart_compare.html'
            context = {
                'serries': chart_serries,
                'chart_container_name': 'compare_chart',
            }
            html = render_to_string(template, context, self.request)

        kwargs.update({'html': html})

        return super().form_valid(form, **kwargs)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'index',
            'all_years': len(years()),
            'compare_form': render_to_string(
                template_name=f'{App_name}/includes/compare_form.html',
                context={'form': forms.DrinkCompareForm()},
                request=self.request
            ),
            **H.RenderContext(self.request).context_to_reload(),
        })
        return context


class Lists(ListMixin):
    template_name = 'drinks/index.html'
    model = models.Drink

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab'] = 'data'

        return context


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Summary(IndexMixin):
    def get_context_data(self, **kwargs):
        qs = list(models.Drink.objects.summary())
        drink_years = [x['year'] for x in qs]

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'drinks_categories': drink_years,
            'drinks_data_ml': [x['per_day'] for x in qs],
            'drinks_data_alcohol': [x['qty'] * 0.025 for x in qs],
            'drinks_cnt': len(drink_years) - 1.5,
        })
        return context


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Delete(DeleteAjaxMixin):
    model = models.Drink


class TargetLists(DispatchListsMixin, ListMixin):
    model = models.DrinkTarget


class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
