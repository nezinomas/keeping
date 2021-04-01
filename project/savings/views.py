from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin, IndexMixin,
                                 ListMixin, UpdateAjaxMixin)
from ..pensions.views import Lists as PensionLists
from ..pensions.views import TypeLists as PensionTypeLists
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['savings'] = Lists.as_view()(
            self.request,
            as_string=True)
        context['categories'] = TypeLists.as_view()(
            self.request,
            as_string=True)

        context['pension_type'] = PensionTypeLists.as_view()(
            self.request,
            as_string=True)
        context['pension'] = PensionLists.as_view()(
            self.request,
            as_string=True)

        return context


# ----------------------------------------------------------------------------
#                                                                 Saving Views
# ----------------------------------------------------------------------------
class Lists(ListMixin):
    model = models.Saving


class New(CreateAjaxMixin):
    model = models.Saving
    form_class = forms.SavingForm


class Update(UpdateAjaxMixin):
    model = models.Saving
    form_class = forms.SavingForm


class Delete(DeleteAjaxMixin):
    model = models.Saving


# ----------------------------------------------------------------------------
#                                                            Saving Type Views
# ----------------------------------------------------------------------------
class TypeLists(ListMixin):
    model = models.SavingType

    def get_queryset(self):
        return models.SavingType.objects.related()


class TypeNew(CreateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
