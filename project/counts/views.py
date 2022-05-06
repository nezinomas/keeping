from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.date import weeknumber
from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, RedirectViewMixin,
                                 TemplateViewMixin, UpdateViewMixin,
                                 rendered_content)
from .forms import CountForm, CountTypeForm
from .lib.views_helper import ContextMixin, CounTypetObjectMixin
from .models import Count, CountType


class Redirect(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        qs = None
        slug = kwargs.get('slug')

        try:
            qs = CountType.objects \
                .related() \
                .get(slug=slug)
        except ObjectDoesNotExist:
            qs = CountType.objects \
                .related() \
                .first()

        if not qs:
            url = reverse('counts:empty')
        else:
            url = reverse('counts:index', kwargs={'slug': qs.slug})

        return url


class Empty(TemplateViewMixin):
    template_name = 'counts/empty.html'


class InfoRow(CounTypetObjectMixin, TemplateViewMixin):
    template_name = 'counts/info_row.html'

    def get_context_data(self, **kwargs):
        self.object = self.kwargs.get('object')
        if not self.object:
            super().get_object()

        year = self.request.user.year
        week = weeknumber(year)

        qs_total = \
            Count.objects \
            .related() \
            .filter(count_type=self.object, date__year=year) \
            .aggregate(total=Sum('quantity'))
        total = qs_total.get('total') or 0

        try:
            qs_latest = \
                Count.objects \
                .related() \
                .filter(count_type=self.object) \
                .latest()
            gap = (datetime.now().date() - qs_latest.date).days
        except Count.DoesNotExist:
            gap = 0

        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.object.title,
            'week': week,
            'total': total,
            'ratio': total / week,
            'current_gap': gap,
        })
        return context


class Index(CounTypetObjectMixin, TemplateViewMixin):
    template_name = 'counts/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        super().get_object()

        if not self.object:
            return redirect(reverse('counts:redirect'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        super().get_object()
        kwargs['object'] = self.object

        context.update({
            'object': self.object,
            'info_row': rendered_content(self.request, InfoRow, **kwargs),
            'tab_content': rendered_content(self.request, TabIndex, **kwargs),
        })
        return context


class TabIndex(CounTypetObjectMixin, ContextMixin, TemplateViewMixin):
    template_name = 'counts/tab_index.html'

    def get_year(self):
        return self.request.user.year

    def get_queryset(self):
        self.object = self.kwargs.get('object')
        if not self.object:
            super().get_object()

        year = self.get_year()
        count_type = self.object.slug

        return \
            Count.objects \
            .sum_by_day(year=year, count_type=count_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        calendar_data = self.render_context.calender_data

        context.update({
            'object': self.object,
            'chart_calendar_1H': \
                self.render_context.chart_calendar(calendar_data[0:6], '1H'),
            'chart_calendar_2H': \
                self.render_context.chart_calendar(calendar_data[6:], '2H'),
            'chart_weekdays': \
                self.render_context.chart_weekdays(),
            'chart_months': \
                self.render_context.chart_months(),
            'chart_histogram': \
                self.render_context.chart_histogram(),
        })
        return context


class TabData(ListViewMixin):
    model = Count
    template_name = 'counts/tab_list.html'

    def get_queryset(self):
        year = self.request.user.year
        slug = self.kwargs.get('slug')

        return \
            Count.objects \
            .year(year=year, count_type=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'count_type_slug': self.kwargs.get('slug'),
        })
        return context


class TabHistory(ContextMixin, TemplateViewMixin):
    template_name = 'counts/tab_history.html'

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return Count.objects.items(count_type=slug)

    def get_year(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'count_type_slug': self.kwargs.get('slug'),
            'chart_weekdays': self.render_context.chart_weekdays(_('Days of week')),
            'chart_years': self.render_context.chart_years(),
            'chart_histogram': self.render_context.chart_histogram(),
        })
        return context


class CountUrlMixin():
    def get_success_url(self):
        slug = self.object.count_type.slug
        return reverse_lazy('counts:tab_data', kwargs={'slug': slug})


class New(CountUrlMixin, CreateViewMixin):
    model = Count
    form_class = CountForm

    def get_hx_trigger(self):
        tab = self.kwargs.get('tab')

        if tab in ['index', 'data', 'history']:
            return f'reload{tab.title()}'

        return 'reloadData'

    def url(self):
        count_type_slug = self.kwargs.get('slug')
        tab = self.kwargs.get('tab')

        if tab not in ['index', 'data', 'history']:
            tab = 'index'

        return reverse_lazy('counts:new', kwargs={'slug': count_type_slug, 'tab': tab})


class Update(CountUrlMixin, UpdateViewMixin):
    model = Count
    form_class = CountForm
    hx_trigger = 'reloadData'


class Delete(CountUrlMixin, DeleteViewMixin):
    model = Count
    hx_trigger = 'reloadData'


# ---------------------------------------------------------------------------------------
#                                                                             Count Types
# ---------------------------------------------------------------------------------------
class TypeUrlMixin():
    def get_hx_redirect(self):
        return self.get_success_url()

    def get_success_url(self):
        slug = self.object.slug
        return reverse_lazy('counts:index', kwargs={'slug': slug})


class TypeNew(TypeUrlMixin, CreateViewMixin):
    model = CountType
    form_class = CountTypeForm
    hx_trigger = 'afterType'
    url = reverse_lazy('counts:type_new')


class TypeUpdate(TypeUrlMixin, UpdateViewMixin):
    model = CountType
    form_class = CountTypeForm
    hx_trigger = 'afterType'


class TypeDelete(TypeUrlMixin, DeleteViewMixin):
    model = CountType
    hx_trigger = 'afterType'
    hx_redirect = reverse_lazy('counts:redirect')
