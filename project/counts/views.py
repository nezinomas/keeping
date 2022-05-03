from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, RedirectViewMixin,
                                 TemplateViewMixin, UpdateViewMixin)
from .forms import CountForm, CountTypeForm
from .lib.views_helper import ContextMixin
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


class Index(ContextMixin, TemplateViewMixin):
    def get_template_names(self):
        if self.request.htmx:
            return ['counts/tab_index.html']
        else:
            return ['counts/index.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        count_type_object = context['object']

        calendar_data = self.render_context.calender_data

        context.update({
            'tab': 'index',
            'info_row': \
                self.render_context.info_row(title=count_type_object.title),
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


class Lists(ContextMixin, ListViewMixin):
    model = Count

    def get_template_names(self):
        if self.request.htmx:
            return ['counts/tab_list.html']
        else:
            return ['counts/index.html']

    def get_queryset(self):
        year = self.request.user.year
        slug = self.kwargs.get('slug')

        return \
            Count.objects \
            .year(year=year, count_type=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        count_type_object = context['object']

        context.update({
            'tab': 'list',
            'info_row': \
                self.render_context.info_row(title=count_type_object.title),
        })
        return context


class History(ContextMixin, TemplateViewMixin):
    def get_template_names(self):
        if self.request.htmx:
            return ['counts/tab_history.html']
        else:
            return ['counts/index.html']

    def get_qs(self):
        slug = self.kwargs.get('slug')
        return Count.objects.items(count_type=slug)

    def get_year(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'info_row': f'<h6>{_("Historical data")}</h6>',
            'chart_weekdays': self.render_context.chart_weekdays(_('Days of week')),
            'chart_years': self.render_context.chart_years(),
            'chart_histogram': self.render_context.chart_histogram(),
        })
        return context


class CountUrlMixin():
    def get_success_url(self):
        slug = self.object.count_type.slug
        url = reverse_lazy('counts:list', kwargs={'slug': slug})
        return url


class New(CountUrlMixin, CreateViewMixin):
    model = Count
    form_class = CountForm

    def url(self):
        slug = self.kwargs.get('slug')
        return reverse_lazy('counts:new', kwargs={'slug': slug})


class Update(CountUrlMixin, UpdateViewMixin):
    model = Count
    form_class = CountForm


class Delete(CountUrlMixin, DeleteViewMixin):
    model = Count


# ---------------------------------------------------------------------------------------
#                                                                             Count Types
# ---------------------------------------------------------------------------------------
class TypeUrlMixin():
    def get_hx_redirect(self):
        return self.get_success_url()

    def get_success_url(self):
        slug = self.object.slug
        return reverse_lazy('counts:list', kwargs={'slug': slug})


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
