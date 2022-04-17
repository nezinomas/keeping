from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchListsMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models


class Lists(DispatchListsMixin, ListMixin):
    model = models.Pension


class New(CreateAjaxMixin):
    model = models.Pension
    form_class = forms.PensionForm


class Update(UpdateAjaxMixin):
    model = models.Pension
    form_class = forms.PensionForm


class Delete(DeleteAjaxMixin):
    model = models.Pension


class TypeLists(DispatchListsMixin, ListMixin):
    model = models.PensionType


class TypeNew(CreateAjaxMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
