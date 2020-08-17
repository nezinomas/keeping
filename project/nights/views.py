from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView

from ..core.mixins.views import CreateAjaxMixin, IndexMixin, UpdateAjaxMixin
from .apps import App_name
from .forms import NightForm as Form
from .lib.stats import Stats
from .lib.views_helper import RenderContext, UpdateLinkMixin
from .models import Night as Counter


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = Counter.objects.sum_by_day(year=year)
        r = RenderContext(self.request, Stats(year=year, data=qs))

        context = super().get_context_data(**kwargs)
        context.update({
            **r.context_url_names(),
            **r.context_to_reload(year)
        })
        return context


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = Counter.objects.year(year)
        r = RenderContext(self.request, Stats(year=year, data=qs))

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'data',
            'info_row': r.info_row(year),
            'data': r.list_data(),
            **r.context_url_names()
        })
        return context


class New(UpdateLinkMixin, CreateAjaxMixin):
    model = Counter
    form_class = Form


class Update(UpdateLinkMixin, UpdateAjaxMixin):
    model = Counter
    form_class = Form


class History(IndexMixin):
    def get_context_data(self, **kwargs):
        qs = Counter.objects.items()
        r = RenderContext(self.request, Stats(data=qs))

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'chart_weekdays': r.chart_weekdays('Savaitės dienos'),
            'chart_years': r.chart_years(),
            'chart_histogram': r.chart_histogram(),
            **r.context_url_names()
        })
        return context


class ReloadStats(TemplateView):
    template_name = f'{App_name}/includes/reload_stats.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            request.GET['ajax_trigger']
        except KeyError:
            return redirect(reverse(f'{App_name}:{App_name}_index'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        year = request.user.year
        qs = Counter.objects.sum_by_day(year=year)
        r = RenderContext(self.request, Stats(year=year, data=qs))
        context = r.context_to_reload(year)

        return self.render_to_response(context=context)
