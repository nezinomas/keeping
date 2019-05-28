from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import IncomeForm, IncomeTypeForm
from .models import Income, IncomeType


def _items(request):
    qs = (
        Income.objects.
        filter(date__year=request.request.user.profile.year).
        prefetch_related('account')
    )
    return qs


def _json_response(request, obj):
    obj.form_template = 'incomes/includes/partial_incomes_form.html'
    obj.items_template = 'incomes/includes/partial_incomes_list.html'

    obj.items = _items(request)

    return obj.GenJsonResponse()


def lists(request):
    qs = _items(request)

    form = IncomeForm()
    context = {
        'objects': qs,
        'categories': type_lists(request),
        'form': form
    }

    return render(request, 'incomes/incomes_list.html', context=context)


def new(request):
    form = IncomeForm(request.POST or None)
    context = {
        'url': reverse('incomes:incomes_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Income, pk=pk)
    form = IncomeForm(request.POST or None, instance=object)
    url = reverse(
        'incomes:incomes_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


# IncomeType helper functions and views

def _type_items():
    return IncomeType.objects.all()


def _type_json_response(obj):
    obj.form_template = 'incomes/includes/partial_incomes_type_form.html'
    obj.items_template = 'incomes/includes/partial_incomes_type_list.html'

    obj.items_template_var_name = 'categories'
    obj.items = _type_items()

    return obj.GenJsonResponse()


def type_lists(request):
    qs = _type_items()
    return render_to_string(
        'incomes/includes/partial_incomes_type_list.html',
        {'categories': qs},
        request,
    )


def type_new(request):
    form = IncomeTypeForm(request.POST or None)
    context = {
        'url': reverse('incomes:incomes_type_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _type_json_response(obj)


def type_update(request, pk):
    object = get_object_or_404(IncomeType, pk=pk)
    form = IncomeTypeForm(request.POST or None, instance=object)
    url = reverse(
        'incomes:incomes_type_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _type_json_response(obj)
