from datetime import datetime

from django.db.models import F
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ...core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                  ListViewMixin, SearchMixin,
                                  TemplateViewMixin, UpdateViewMixin)
from .. import forms, models


class GetMonthMixin():
    def get_month(self):
        month = self.request.GET.get('month')
        now = datetime.now().month

        try:
            month = int(month)
        except (ValueError, TypeError):
            month = now

        return month


class Index(GetMonthMixin, TemplateViewMixin):
    template_name = 'expenses/index.html'


class Lists(GetMonthMixin, ListViewMixin):
    model = models.Expense
    template_name = 'expenses/includes/list.html'

    def get_queryset(self):
        month = self.get_month()
        qs = super().get_queryset()

        if month in range(1, 13):
            qs = qs.filter(date__month=month)

        qs = qs.order_by('-date', 'expense_type', F('expense_name').asc())

        return qs

    def get_context_data(self, **kwargs):
        month = self.get_month()

        notice = _('There are no records for month <b>%(month)s</b>.') % {'month': month}
        if month == '13' or not month:
            notice = _('No records in <b>%(year)s</b>.') % {'year': self.request.user.year}

        context = super().get_context_data(**kwargs)
        context.update({
            'notice': notice,
        })
        return context


class New(CreateViewMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    success_url = reverse_lazy('expenses:list')


class Update(UpdateViewMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    success_url = reverse_lazy('expenses:list')


class Delete(DeleteViewMixin):
    model = models.Expense
    success_url = reverse_lazy('expenses:list')


class Search(SearchMixin):
    template_name = 'expenses/expense_list.html'
    per_page = 50

    search_method = 'search_expenses'


class LoadExpenseName(ListViewMixin):
    template_name = 'core/dropdown.html'

    def get(self, request, *args, **kwargs):
        objects = []
        pk = request.GET.get('expense_type')

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = None

        if pk:
            objects = (
                models.ExpenseName
                .objects
                .parent(pk)
                .year(request.user.year)
            )

        return self.render_to_response({'objects': objects})
