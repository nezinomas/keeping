from ..core.mixins.views import CreateAjaxMixin, ListMixin, UpdateAjaxMixin, IndexMixin
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['savings'] = Lists.as_view()(self.request, as_string=True)
        context['categories'] = TypeLists.as_view()(self.request, as_string=True)

        return context


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
class GetItems():
    def get_queryset(self):
        return models.SavingType.objects.items(show_all=True)


class TypeLists(GetItems, ListMixin):
    model = models.SavingType


class TypeNew(GetItems, CreateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm


class TypeUpdate(GetItems, UpdateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
