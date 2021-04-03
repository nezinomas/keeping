from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin, IndexMixin,
                                 ListMixin, UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['data'] = Lists.as_view()(
            self.request, as_string=True)
        context['categories'] = TypeLists.as_view()(
            self.request, as_string=True)

        return context


#----------------------------------------------------------------------------------------
#                                                                           Pension views
#----------------------------------------------------------------------------------------
class Lists(ListMixin):
    model = models.Pension


class New(CreateAjaxMixin):
    model = models.Pension
    form_class = forms.PensionForm


class Update(UpdateAjaxMixin):
    model = models.Pension
    form_class = forms.PensionForm


class Delete(DeleteAjaxMixin):
    model = models.Pension


#----------------------------------------------------------------------------------------
#                                                                       PensionType views
#----------------------------------------------------------------------------------------
class TypeLists(ListMixin):
    model = models.PensionType


class TypeNew(CreateAjaxMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
