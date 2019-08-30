from django.shortcuts import render

from ...core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                  UpdateAjaxMixin)
from .. import forms, models
from ..views.expenses_type import Lists as TypeLists


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TypeLists.as_view()(
            self.request, as_string=True)
        context['expenses'] = Lists.as_view()(
            self.request, as_string=True)

        return context


class Lists(ListMixin):
    model = models.Expense


class New(CreateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm


class Update(UpdateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = models.ExpenseName.objects.parent(pk).year(request.user.profile.year)

    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )
