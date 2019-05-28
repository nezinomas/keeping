from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin

from .models import Saving, SavingType
from .forms import SavingForm, SavingTypeForm


# Saving views
def _items(request):
    qs = (
        Saving.objects.
        filter(date__year=request.user.profile.year).
        prefetch_related('account', 'saving_type')
    )
    return qs


def _json_response(request, obj):
    obj.form_template = 'savings/includes/partial_savings_form.html'
    obj.items_template = 'savings/includes/partial_savings_list.html'

    obj.items = _items(request)

    return obj.GenJsonResponse()


def lists(request):
    qs = _items(request)

    form = SavingForm()
    context = {
        'objects': qs,
        'categories': type_lists(request),
        'form': form
    }

    return render(request, 'savings/savings_list.html', context=context)


def new(request):
    form = SavingForm(request.POST or None)
    context = {
        'url': reverse('savings:savings_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Saving, pk=pk)
    form = SavingForm(request.POST or None, instance=object)
    url = reverse(
        'savings:savings_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


# Saving Type views
def _type_items():
    return SavingType.objects.all()


def _type_json_response(obj):
    obj.form_template = 'savings/includes/partial_savings_type_form.html'
    obj.items_template = 'savings/includes/partial_savings_type_list.html'

    obj.items_template_var_name = 'categories'
    obj.items = _type_items()

    return obj.GenJsonResponse()


def type_lists(request):
    qs = _type_items()
    return render_to_string(
        'savings/includes/partial_savings_type_list.html',
        {'categories': qs},
        request,
    )


def type_new(request):
    form = SavingTypeForm(request.POST or None)
    context = {
        'url': reverse('savings:savings_type_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _type_json_response(obj)


def type_update(request, pk):
    object = get_object_or_404(SavingType, pk=pk)
    form = SavingTypeForm(request.POST or None, instance=object)
    url = reverse(
        'savings:savings_type_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _type_json_response(obj)
