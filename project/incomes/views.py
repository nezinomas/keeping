from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


@login_required()
def index(request):
    context = {
        'incomes': Lists.as_view()(request, as_string=True),
        'categories': TypeLists.as_view()(request, as_string=True),
    }
    return render(request, 'incomes/incomes_list.html', context)


#
# Income views
#
class Lists(ListMixin):
    model = models.Income


class New(CreateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


class Update(UpdateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


#
# IncomeType views
#
class TypeLists(ListMixin):
    model = models.IncomeType


class TypeNew(CreateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm
