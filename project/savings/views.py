from django.urls import reverse_lazy

from ..core.lib.convert_price import ConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from ..pensions import views as pension_views
from . import forms, models


class Index(TemplateViewMixin):
    template_name = "savings/index.html"

    def get_context_data(self, **kwargs):
        context = {
            "saving": rendered_content(self.request, Lists),
            "saving_type": rendered_content(self.request, TypeLists),
            "pension": rendered_content(self.request, pension_views.Lists),
            "pension_type": rendered_content(self.request, pension_views.TypeLists),
        }

        return {**super().get_context_data(**kwargs), **context}


class Lists(ListViewMixin):
    model = models.Saving

    def get_queryset(self):
        return models.Saving.objects.year(year=self.request.user.year)


class New(CreateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    hx_trigger_form = "reload"
    success_url = reverse_lazy("savings:list")


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:list")


class Delete(DeleteViewMixin):
    model = models.Saving
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:list")


class TypeLists(ListViewMixin):
    model = models.SavingType

    def get_queryset(self):
        return models.SavingType.objects.related()


class TypeNew(CreateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
    hx_trigger_django = "afterType"

    url = reverse_lazy("savings:type_new")
    success_url = reverse_lazy("savings:type_list")


class TypeUpdate(UpdateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
    hx_trigger_django = "afterType"
