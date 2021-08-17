from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import RedirectView, TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin,
                                 UpdateAjaxMixin)
from .forms import CountForm as Form
from .forms import CountTypeForm
from .lib.stats import Stats
from .lib.views_helper import RenderContext
from .models import Count as Counter
from .models import CountType


def get_count_object(kwargs):
    pk = 0
    slug = 'counter'

    try:
        obj = CountType.objects.related().get(slug=kwargs.get('count_type'))
        pk = obj.pk
        slug = obj.slug
    except ObjectDoesNotExist:
        pass

    return (pk, slug)


class ContextMixin():
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = Counter.objects.sum_by_day(year=year)
        r = RenderContext(self.request, Stats(year=year, data=qs))

        context = super().get_context_data(**kwargs)
        pk, slug = get_count_object(kwargs)
        context.update({
            **r.context_to_reload(year),
            'count_type': slug,
            'count_id': pk,
            'records': qs.count(),
        })

        return context


class Index(ContextMixin, IndexMixin):
    pass


class Redirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        qs = None
        count_id = kwargs.get('count_id')

        try:
            qs = CountType.objects.related().get(pk=count_id)
        except ObjectDoesNotExist:
            qs = CountType.objects.related().first()

        if not qs:
            url = reverse('counts:counts_empty')
        else:
            url = reverse('counts:counts_index', kwargs={'count_type': qs.slug})

        return url


class CountsEmpty(IndexMixin):
    template_name = 'counts/counts_empty.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk, slug = get_count_object(kwargs)
        context.update({
            'count_type': slug,
            'count_id': pk,
        })
        return context


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = Counter.objects.year(year)
        r = RenderContext(self.request, Stats(year=year, data=qs))

        context = super().get_context_data(**kwargs)
        pk, slug = get_count_object(kwargs)
        context.update({
            'tab': 'data',
            'count_type': slug,
            'count_id': pk,
            'info_row': r.info_row(year),
            'data': r.list_data(),
            'records': qs.count(),
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
        pk, slug = get_count_object(kwargs)
        context.update({
            'tab': 'history',
            'count_type': slug,
            'count_id': pk,
            'chart_weekdays': r.chart_weekdays(_('Days of week')),
            'chart_years': r.chart_years(),
            'chart_histogram': r.chart_histogram(),
            'records': qs.count(),
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
