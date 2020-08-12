from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView

from ..core.mixins.views import CreateAjaxMixin, IndexMixin, UpdateAjaxMixin
from . import forms, models
from .apps import App_name
from .lib import views_helper as H
from .lib.stats import Stats
from .lib.views_helper import UpdateLinkMixin


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            **H.context_url_names(),
            **H.context_to_reload(self.request)
        })
        return context


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        qs = models.Night.objects.year(year)
        obj = Stats(year=year, data=qs)

        context.update({
            'tab': 'data',
            'info_row': H.render_info_row(self.request, obj, year),
            'data': H.render_list_data(self.request, obj.items()),
            **H.context_url_names()
        })
        return context


class New(UpdateLinkMixin, CreateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class Update(UpdateLinkMixin, UpdateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class History(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = models.Night.objects.items()
        obj = Stats(data=qs)

        context.update({
            'tab': 'history',
            'chart_weekdays': H.render_chart_weekdays(self.request, obj, 'Savaitės dienos'),
            'chart_years': H.render_chart_years(self.request, obj.year_totals(), 'Metai'),
            'chart_histogram': H.render_chart_histogram(self.request, obj.gaps()),
            **H.context_url_names()
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
        context = H.context_to_reload(request)
        return self.render_to_response(context)
