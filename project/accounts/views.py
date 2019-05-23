from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin
from .models import Account


def _items():
    return Account.objects.all()


def new(request):
    pass


def update(request, pk):
    pass
