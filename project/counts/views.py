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
    helper = None

    def get_year(self):
        return self.request.user.year

    def get_qs(self):
        return Counter.objects.sum_by_day(year=self.get_year())

    def get_context_data(self, **kwargs):
        pk, slug = get_count_object(kwargs)
        year = self.get_year()
        qs = self.get_qs()

        self.helper = RenderContext(
            self.request,
            Stats(year=year, data=qs)
        )

        context = super().get_context_data(**kwargs)
        context.update({
            'count_type': slug,
            'count_id': pk,
            'records': qs.count(),
        })

        return context


class Index(ContextMixin, IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **self.helper.context_to_reload(self.get_year())
        })

        return context


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
            url = reverse('counts:counts_index',
                          kwargs={'count_type': qs.slug})

        return url


class CountsEmpty(IndexMixin):
    template_name = 'counts/counts_empty.html'

    def get_context_data(self, **kwargs):
        pk, slug = get_count_object(kwargs)

        context = super().get_context_data(**kwargs)
        context.update({
            'count_type': slug,
            'count_id': pk,
        })
        return context


class Lists(ContextMixin, IndexMixin):
    def get_qs(self):
        return Counter.objects.year(self.get_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'data',
            'info_row': self.helper.info_row(self.get_year()),
            'data': self.helper.list_data(),
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


class History(ContextMixin, IndexMixin):
    def get_qs(self):
        return Counter.objects.items()

    def get_year(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'chart_weekdays': self.helper.chart_weekdays(_('Days of week')),
            'chart_years': self.helper.chart_years(),
            'chart_histogram': self.helper.chart_histogram(),
        })
        return context


class ReloadStats(ContextMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'counts/includes/reload_stats.html'
    redirect_view = reverse_lazy('counts:counts_index',
                                 kwargs={'count_type': 'counter'})

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context.update({
            **self.helper.context_to_reload(self.get_year())
        })
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
