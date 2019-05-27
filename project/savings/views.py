from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin

from .models import Saving, SavingType
from .forms import SavingForm, SavingTypeForm


# Saving views
def lists(request):
    pass


def new(request):
    pass


def update(request, pk):
    pass


# Saving Type views
def type_lists(request):
    pass


def type_new(request):
    pass


def type_update(request, pk):
    pass
