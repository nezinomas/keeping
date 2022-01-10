from types import SimpleNamespace

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import RedirectView, TemplateView

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from .forms import CountForm, CountTypeForm
from .lib.views_helper import ContextMixin
from .models import Count, CountType


class Redirect(LoginRequiredMixin, RedirectView):
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


class ReloadStats(LoginRequiredMixin, ContextMixin, DispatchAjaxMixin, TemplateView):
    template_name = 'counts/index.html'
    redirect_view = reverse_lazy('counts:counts_index',
                                 kwargs={'count_type': 'counter'})

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            **self.helper.context_to_reload(
                self.get_year(),
                **{'count_type_object': context['count_type_object']}
            )
        })
        # delete Objects that is not JSON serializable
        context.pop('view')
        context.pop('count_type_object')

        return JsonResponse(context)


class Index(ContextMixin, IndexMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        count_type = request.resolver_match.kwargs.get("count_type")

        if count_type and count_type == 'drinks':
            return redirect(reverse('counts:counts_empty'))

        if count_type:
            qs = CountType.objects.related().filter(slug=count_type)
            if not qs.exists():
                return redirect(reverse('counts:counts_empty'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **self.helper.context_to_reload(
                self.get_year(),
                **{'count_type_object': context['count_type_object']})
        })

        return context


class Lists(ContextMixin, ListMixin):
    template_name = 'counts/index.html'
    model = Count

    def get_qs(self):
        return Count.objects.year(self.get_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = {'count_type_object': context['count_type_object']}
        context.update({
            'tab': 'data',
            'info_row': self.helper.info_row(self.get_year(),**obj),
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        qs = CountType.objects.related().exclude(slug='drinks')
        if qs.exists():
            return redirect(reverse('counts:counts_index', kwargs={'count_type': qs[0].slug}))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'count_type_object': SimpleNamespace(pk=0, title=_('Not found'), slug='counter')
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