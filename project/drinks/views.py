from datetime import datetime

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.date import years
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, RedirectViewMixin,
                                 TemplateViewMixin, UpdateViewMixin,
                                 rendered_content)
from ..counts.lib.stats import Stats as CountStats
from .forms import DrinkCompareForm, DrinkForm, DrinkTargetForm
from .lib import views_helper as H
from .lib.drinks_options import DrinksOptions
from .models import Drink, DrinkTarget, DrinkType


class Index(TemplateViewMixin):
    template_name = 'drinks/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'all_years': len(years()),
            'tab_content': rendered_content(self.request, TabIndex, **kwargs),
            'compare_form': render_to_string(
                template_name='drinks/compare_form.html',
                context={'form': DrinkCompareForm()},
                request=self.request
            ),
            **H.drink_type_dropdown(self.request),
        })
        return context


class TabIndex(TemplateViewMixin):
    template_name = 'drinks/tab_index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        qs = Drink.objects.sum_by_day(year)
        past_latest_record = None

        try:
            qs_past = \
                Drink \
                .objects \
                .related() \
                .filter(date__year__lt=year) \
                .latest()
            past_latest_record = qs_past.date
        except Drink.DoesNotExist:
            pass

        stats = CountStats(year=year, data=qs, past_latest=past_latest_record)
        data = stats.chart_calendar()
        rendered = H.RenderContext(self.request, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'target_list': rendered_content(self.request, TargetLists, **kwargs),
            'chart_quantity': rendered.chart_quantity(),
            'chart_consumption': rendered.chart_consumption(),
            'chart_calendar_1H': rendered.chart_calendar(data[0:6], '1H'),
            'chart_calendar_2H': rendered.chart_calendar(data[6:], '2H'),
            'tbl_consumption': rendered.tbl_consumption(),
            'tbl_last_day': rendered.tbl_last_day(),
            'tbl_alcohol': rendered.tbl_alcohol(),
            'tbl_std_av': rendered.tbl_std_av(),
            'records': qs.count(),
        })
        return context

class TabData(ListViewMixin):
    model = Drink
    template_name = 'drinks/tab_data.html'

    def get_queryset(self):
        year = self.request.user.year
        return Drink.objects.year(year=year)


class TabHistory(TemplateViewMixin):
    template_name = 'drinks/tab_history.html'

    def get_context_data(self, **kwargs):
        drink_years = []
        ml = []
        alcohol = []

        qs = list(Drink.objects.summary())

        obj = DrinksOptions()
        ratio = obj.ratio

        if qs:
            for year in range(qs[0]['year'], datetime.now().year+1):
                drink_years.append(year)

                item = next((x for x in qs if x['year'] == year), False)
                if item:
                    _stdav = item['qty'] / ratio
                    _alkohol = obj.stdav_to_alkohol(stdav=_stdav)

                    alcohol.append(_alkohol)
                    ml.append(item['per_day'])
                else:
                    alcohol.append(0.0)
                    ml.append(0.0)

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'drinks_categories': drink_years,
            'drinks_data_ml': ml,
            'drinks_data_alcohol': alcohol,
            'records': len(drink_years) if len(drink_years) > 1 else 0,
        })
        return context


class HistoricalData(TemplateViewMixin):
    template_name = 'drinks/chart_compare.html'

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
    template_name = 'drinks/compare_form.html'
    form_class = DrinkCompareForm
    form_data_dict = {}

    def form_valid(self, form, **kwargs):
        html = _('No data')
        years_data = [self.form_data_dict['year1'], self.form_data_dict['year2']]
        chart_serries = H.several_years_consumption(years_data)

        if len(chart_serries) == 2:
            template = 'drinks/chart_compare.html'
            context = {
                'serries': chart_serries,
                'chart_container_name': 'compare_chart',
            }
            html = render_to_string(template, context, self.request)

        kwargs.update({'html': html})

        return super().form_valid(form, **kwargs)


class New(CreateViewMixin):
    model = Drink
    form_class = DrinkForm

    def get_hx_trigger(self):
        tab = self.kwargs.get('tab')

        if tab in ['index', 'data', 'history']:
            return f'reload{tab.title()}'

        return 'reloadData'

    def url(self):
        tab = self.kwargs.get('tab')

        if tab not in ['index', 'data', 'history']:
            tab = 'index'

        return reverse_lazy('drinks:new', kwargs={'tab': tab})


class Update(UpdateViewMixin):
    model = Drink
    form_class = DrinkForm
    success_url = reverse_lazy('drinks:tab_data')
    hx_trigger = 'reloadData'

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.quantity * DrinksOptions(drink_type=obj.option).ratio

        return obj


class Delete(DeleteViewMixin):
    model = Drink
    success_url = reverse_lazy('drinks:tab_data')
    hx_trigger = 'reloadData'


class TargetLists(ListViewMixin):
    model = DrinkTarget

    def get_queryset(self):
        obj = DrinksOptions()
        year = self.request.user.year

        qs = DrinkTarget.objects.year(year)
        for q in qs:
            _qty = q.quantity
            q.quantity = obj.stdav_to_ml(stdav=_qty)
            q.max_bottles = obj.stdav_to_bottles(year=year, max_stdav=_qty)

        return qs


class TargetNew(CreateViewMixin):
    model = DrinkTarget
    form_class = DrinkTargetForm
    success_url = reverse_lazy('drinks:index')

    def get_hx_trigger(self):
        tab = self.kwargs.get('tab')

        if tab in ['index', 'data', 'history']:
            return f'reload{tab.title()}'

        return 'reloadIndex'

    def url(self):
        tab = self.kwargs.get('tab')

        if tab not in ['index', 'data', 'history']:
            tab = 'index'

        return reverse_lazy('drinks:target_new', kwargs={'tab': tab})


class TargetUpdate(UpdateViewMixin):
    model = DrinkTarget
    form_class = DrinkTargetForm
    success_url = reverse_lazy('drinks:tab_index')
    hx_trigger = 'reloadIndex'

    def get_object(self):
        obj = super().get_object()

        if obj:
            if obj.drink_type == 'stdav':
                return obj

            obj.quantity = \
                DrinksOptions() \
                .stdav_to_ml(drink_type=obj.drink_type, stdav=obj.quantity)

        return obj


class SelectDrink(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        drink_type = kwargs.get('drink_type')

        if drink_type not in DrinkType.values:
            drink_type = DrinkType.BEER.value

        user = self.request.user
        user.drink_type = drink_type
        user.save()

        return reverse_lazy('drinks:index')
