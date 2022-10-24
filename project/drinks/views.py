import contextlib

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.date import years
from ..core.lib.translation import month_names
from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 FormViewMixin, ListViewMixin,
                                 RedirectViewMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from ..counts.lib.stats import Stats as CountStats
from .forms import DrinkCompareForm, DrinkForm, DrinkTargetForm
from .lib import views_helper as H
from .lib.drinks_options import DrinksOptions
from .lib.drinks_stats import DrinkStats
from .models import Drink, DrinkTarget, DrinkType
from .services.calendar_chart import CalendarChart
from .services.history import HistoryService


class Index(TemplateViewMixin):
    template_name = 'drinks/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab_content': rendered_content(self.request, TabIndex, **kwargs),
            **H.drink_type_dropdown(self.request),
        })
        return context


class TabIndex(TemplateViewMixin):
    template_name = 'drinks/tab_index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        latest_past_date = None
        with contextlib.suppress(Drink.DoesNotExist):
            latest_past_date = \
                Drink.objects \
                .related() \
                .filter(date__year__lt=year) \
                .latest() \
                .date

        latest_current_date = None
        with contextlib.suppress(Drink.DoesNotExist):
            latest_current_date = \
                Drink.objects \
                .year(year) \
                .latest() \
                .date

        qs_by_day = Drink.objects.sum_by_day(year)
        calendar_service = \
            CalendarChart(
                year=year,
                data=qs_by_day,
                latest_past_date=latest_past_date
            )

        qs_by_month = Drink.objects.sum_by_month(year)
        rendered = \
            H.RenderContext(
                request=self.request,
                year=year,
                drink_stats=DrinkStats(qs_by_month),
                latest_past_date=latest_past_date,
                latest_current_date=latest_current_date
            )

        context = {
            'target_list': \
                    rendered_content(self.request, TargetLists, **kwargs),
            'compare_form_and_chart': \
                    rendered_content(self.request, CompareTwo, **kwargs),
            'all_years': len(years()),
            'records': qs_by_month.count(),
            'chart_quantity': rendered.chart_quantity(),
            'chart_consumption': rendered.chart_consumption(),
            'chart_calendar_1H': calendar_service.first_half_of_year(),
            'chart_calendar_2H': calendar_service.second_half_of_year(),
            'tbl_consumption': rendered.tbl_consumption(),
            'tbl_last_day': rendered.tbl_last_day(),
            'tbl_alcohol': rendered.tbl_alcohol(),
            'tbl_std_av': rendered.tbl_std_av(),
        }
        return super().get_context_data(**kwargs) | context


class TabData(ListViewMixin):
    model = Drink
    template_name = 'drinks/tab_data.html'

    def get_queryset(self):
        year = self.request.user.year
        return Drink.objects.year(year=year)


class TabHistory(TemplateViewMixin):
    template_name = 'drinks/tab_history.html'

    def get_context_data(self, **kwargs):
        data = Drink.objects.sum_by_year()
        obj = HistoryService(data)

        context = {
            'tab': 'history',
            'records': len(obj.years) if len(obj.years) > 1 else 0,
            'chart': {
                'categories': obj.years,
                'data_ml': obj.per_day,
                'data_alcohol': obj.alcohol,
                'text': {
                    'title': _('Drinks'),
                    'per_day': _('Average per day, ml'),
                    'per_year': _('Pure alcohol per year, L'),
                }
            }
        }
        return super().get_context_data(**kwargs) | context


class Compare(TemplateViewMixin):
    template_name = 'drinks/includes/history.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year + 1
        qty = kwargs.get('qty', 0)
        chart_serries = H.several_years_consumption(range(year - qty, year))

        return {
            'chart': {
                'categories': list(month_names().values()),
                'serries': chart_serries,
            },
        }


class CompareTwo(FormViewMixin):
    form_class = DrinkCompareForm
    template_name = 'drinks/includes/compare_form.html'
    success_url = reverse_lazy('drinks:compare_two')

    def form_valid(self, form, **kwargs):
        context = {}
        year1 = form.cleaned_data['year1']
        year2 = form.cleaned_data['year2']
        chart_serries = H.several_years_consumption([year1, year2])

        if len(chart_serries) == 2:
            context |= {
                'form': form,
                'chart': {
                    'categories': list(month_names().values()),
                    'serries': chart_serries,
                },
            }
        return render(self.request, self.template_name, context)


class New(CreateViewMixin):
    model = Drink
    form_class = DrinkForm
    success_url = reverse_lazy('drinks:tab_data')

    def get_hx_trigger_django(self):
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
    hx_trigger_django = 'reloadData'
    success_url = reverse_lazy('drinks:tab_data')

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.quantity * DrinksOptions(drink_type=obj.option).ratio

        return obj


class Delete(DeleteViewMixin):
    model = Drink
    hx_trigger_django = 'reloadData'
    success_url = reverse_lazy('drinks:tab_data')


class TargetLists(ListViewMixin):
    model = DrinkTarget

    def get_queryset(self):
        year = self.request.user.year
        return super().get_queryset().year(year)


class TargetNew(CreateViewMixin):
    model = DrinkTarget
    form_class = DrinkTargetForm
    success_url = reverse_lazy('drinks:index')

    def get_hx_trigger_django(self):
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
    hx_trigger_django = 'reloadIndex'
    success_url = reverse_lazy('drinks:tab_index')

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
