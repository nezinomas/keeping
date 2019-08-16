from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models


@login_required()
def index(request):
    context = {
        'savings': Lists.as_view()(request, as_string=True),
        'categories': TypeLists.as_view()(request, as_string=True),
    }
    return render(request, 'savings/savings_list.html', context)


#
# Saving views
#
class Lists(ListMixin):
    model = models.Saving


class New(CreateAjaxMixin):
    model = models.Saving
    form_class = forms.SavingForm


class Update(UpdateAjaxMixin):
    model = models.Saving
    form_class = forms.SavingForm


#
# SavingType views
#
class TypeLists(ListMixin):
    model = models.SavingType


class TypeNew(CreateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
