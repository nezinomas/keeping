from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from vanilla import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from .create_update import CreateUpdateMixin
from .delete import DeleteMixin
from .kwargs import AddUserToKwargsMixin
from .queryset import GetQuerysetMixin
from .search import SearchMixin


class CreateViewMixin(
    AddUserToKwargsMixin, GetQuerysetMixin, CreateUpdateMixin, CreateView
):
    template_name = "core/generic_form.html"
    form_action = "insert"
    url_name = None

    def url(self):
        app = self.request.resolver_match.app_name
        url_name = self.url_name or "new"
        return reverse_lazy(f"{app}:{url_name}")


class UpdateViewMixin(
    AddUserToKwargsMixin, GetQuerysetMixin, CreateUpdateMixin, UpdateView
):
    template_name = "core/generic_form.html"
    form_action = "update"
    url_name = None

    def url(self):
        app = self.request.resolver_match.app_name
        url_name = self.url_name or "update"
        return (
            reverse_lazy(f"{app}:{url_name}", kwargs={"pk": self.object.pk})
            if self.object
            else None
        )


class DeleteViewMixin(AddUserToKwargsMixin, GetQuerysetMixin, DeleteMixin, DeleteView):
    template_name = "core/generic_delete_form.html"
    url_name = None

    def url(self):
        app = self.request.resolver_match.app_name
        url_name = self.url_name or "delete"
        return (
            reverse_lazy(f"{app}:{url_name}", kwargs={"pk": self.object.pk})
            if self.object
            else None
        )


class RedirectViewMixin(RedirectView):
    pass


class TemplateViewMixin(TemplateView):
    pass


class ListViewMixin(GetQuerysetMixin, ListView):
    pass


class FormViewMixin(AddUserToKwargsMixin, FormView):
    template_name = "core/generic_form.html"


class SearchViewMixin(AddUserToKwargsMixin, SearchMixin, TemplateView):
    pass
