from django.shortcuts import get_object_or_404, reverse
from django.template.loader import render_to_string

from ..accounts.views import lists
from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import TransactionForm
from .models import Transaction


def lists(request):
    pass


def new(request):
    pass


def update(request, pk):
    pass
