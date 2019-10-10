from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.views_helper import context_to_reload


def reload_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    context = {}
    name = 'drinks/includes/reload_stats.html'

    context_to_reload(request, context)

    if ajax_trigger:
        return render(template_name=name, context=context, request=request)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.profile.year
        qs_target = models.DrinkTarget.objects.year(year)

        context = super().get_context_data(**kwargs)
        context_to_reload(self.request, context)

        context['drinks_list'] = Lists.as_view()(
            self.request, as_string=True)

        context['target_list'] = render_to_string(
            'drinks/includes/drinks_target_list.html',
            {'items': qs_target},
            self.request)

        return context


class Lists(ListMixin):
    model = models.Drink


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class TargetLists(ListMixin):
    model = models.DrinkTarget


class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
