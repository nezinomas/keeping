from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import RedirectView, TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin,
                                 UpdateAjaxMixin)
from .forms import CountForm, CountTypeForm
from .lib.views_helper import ContextMixin, get_object
from .models import Count, CountType


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


class ReloadStats(ContextMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'counts/includes/reload_stats.html'
    redirect_view = reverse_lazy('counts:counts_index',
                                 kwargs={'count_type': 'counter'})

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context.update({
            **self.helper.context_to_reload(
                self.get_year(),
                **{'count_title': context['count_title']}
            )
        })
        return self.render_to_response(context=context)


class Index(ContextMixin, IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **self.helper.context_to_reload(
                self.get_year(),
                **{'count_title': context['count_title']})
        })

        return context


class Lists(ContextMixin, IndexMixin):
    def get_qs(self):
        return Count.objects.year(self.get_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'data',
            'info_row': self.helper.info_row(self.get_year()),
            'data': self.helper.list_data(),
        })
        return context


class History(ContextMixin, IndexMixin):
    def get_qs(self):
        return Count.objects.items()

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


class CountsEmpty(IndexMixin):
    template_name = 'counts/counts_empty.html'

    def get_context_data(self, **kwargs):
        obj = get_object(kwargs)

        context = super().get_context_data(**kwargs)
        context.update({
            'count_type': obj.slug,
            'count_id': obj.pk,
        })
        return context


class New(CreateAjaxMixin):
    model = Count
    form_class = CountForm


class Update(UpdateAjaxMixin):
    model = Count
    form_class = CountForm


class Delete(DeleteAjaxMixin):
    model = Count


class TypeNew(CreateAjaxMixin):
    model = CountType
    form_class = CountTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = CountType
    form_class = CountTypeForm


class TypeDelete(DeleteAjaxMixin):
    model = CountType
    form_class = CountTypeForm
