from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin,
                                 UpdateAjaxMixin)
from .forms import CountForm as Form
from .forms import CountTypeForm
from .lib.stats import Stats
from .lib.views_helper import RenderContext
from .models import Count as Counter
from .models import CountType


class ContextMixin():
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = Counter.objects.sum_by_day(year=year)
        r = RenderContext(self.request, Stats(year=year, data=qs))

        context = super().get_context_data(**kwargs)
        context.update({
            **r.context_to_reload(year)
        })

        return context


class Index(ContextMixin, IndexMixin):
    pass


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
        })
        return context


class New(CreateAjaxMixin):
    model = Counter
    form_class = Form


class Update(UpdateAjaxMixin):
    model = Counter
    form_class = Form


class Delete(DeleteAjaxMixin):
    model = Counter


class History(IndexMixin):
    def get_context_data(self, **kwargs):
        qs = Counter.objects.items()
        r = RenderContext(self.request, Stats(data=qs))

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'chart_weekdays': r.chart_weekdays(_('Days of week')),
            'chart_years': r.chart_years(),
            'chart_histogram': r.chart_histogram(),
        })
        return context



class ReloadStats(ContextMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'counts/includes/reload_stats.html'
    redirect_view = reverse_lazy('counts:counts_index', kwargs={'count_type': 'counter'})

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        return self.render_to_response(context=context)


class TypeNew(CreateAjaxMixin):
    model = CountType
    form_class = CountTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = CountType
    form_class = CountTypeForm


class TypeDelete(DeleteAjaxMixin):
    model = CountType
    form_class = CountTypeForm
