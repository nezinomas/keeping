from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.views import CreateAjaxMixin, IndexMixin, UpdateAjaxMixin
from . import forms, models
from .apps import App_name
from .lib.stats import Stats
from .lib import views_helper as H


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        H.context_url_names(context)

        return H.context_to_reload(self.request, year, context)


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        qs = models.Night.objects.year(year)
        obj = Stats(year=year, data=qs)

        H.context_info_row(self.request, obj, year, context)
        H.context_url_names(context)

        context['tab'] = 'data'
        context['data'] = render_to_string(
            f'{App_name}/includes/{App_name}_list.html',
            {
                'items': obj.items(),
                'url_update': f'{App_name}:{App_name}_update',
            },
            self.request
        )
        return context


class New(CreateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class Update(UpdateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class History(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = models.Night.objects.items()
        obj = Stats(data=qs)

        H.context_url_names(context)

        context.update({
            'tab': 'history',
            'chart_weekdays': H.render_chart_weekdays(self.request, obj, 'Savaitės dienos'),
            'chart_years': H.render_chart_years(self.request, obj.year_totals(), 'Metai'),
        })

        gaps = obj.gaps()
        context['chart_histogram'] = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': list(gaps.values()),
                'categories': [f'{x}d' for x in gaps.keys()],
                'chart': 'chart_histogram',
                'chart_title': 'Tarpų dažnis, dienomis',
                'chart_column_color': '196, 37, 37',
            },
            self.request
        )

        return context

def reload_stats(request):
    try:
        request.GET['ajax_trigger']
    except KeyError:
        return redirect(reverse(f'{App_name}:{App_name}_index'))

    return render(
        request=request,
        template_name=f'{App_name}/includes/reload_stats.html',
        context=H.context_to_reload(request, request.user.year)
    )
