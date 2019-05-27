from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin

from .models import Saving, SavingType
from .forms import SavingForm, SavingTypeForm


# Saving views
def _items(request):
    qs = (
        Saving.objects.
        filter(date__year=request.session['year']).
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
    pass


def update(request, pk):
    pass


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
    pass


def type_update(request, pk):
    pass
