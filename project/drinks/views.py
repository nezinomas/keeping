from django.shortcuts import get_object_or_404, render, reverse

from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import DrinkForm
from .models import Drink


def _json_response(request, obj):
    obj.form_template = 'drinks/includes/partial_drinks_form.html'
    obj.items_template = 'drinks/includes/partial_drinks_list.html'

    obj.items = Drink.objects.items(request.user.profile.year)

    return obj.GenJsonResponse()


def lists(request):
    qs = Drink.objects.items(request.user.profile.year)

    form = DrinkForm()
    context = {
        'objects': qs,
        'form': form
    }

    return render(request, 'drinks/drinks_list.html', context=context)


def new(request):
    form = DrinkForm(request.POST or None)
    context = {
        'url': reverse('drinks:drinks_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)


def update(request, pk):
    object = get_object_or_404(Drink, pk=pk)
    form = DrinkForm(request.POST or None, instance=object)
    url = reverse(
        'drinks:drinks_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _json_response(request, obj)
