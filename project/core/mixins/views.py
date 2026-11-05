from django.urls import reverse_lazy
from vanilla import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from ..lib.utils import int_or_zero
from .create_update import CreateUpdateMixin
from .delete import DeleteMixin
from .kwargs import FormKwargsMixin
from .queryset import GetQuerysetMixin
from .search import SearchMixin


class CreateViewMixin(FormKwargsMixin, CreateUpdateMixin, CreateView):
    template_name = "core/generic_form.html"
    form_action = "insert"
    url_name = "new"

    def url(self):
        app = self.request.resolver_match.app_name
        return reverse_lazy(f"{app}:{self.url_name}")


class ObjectUrlMixin:
    """The view's url for its own object, under the request's app."""

    def url(self):
        app = self.request.resolver_match.app_name
        return reverse_lazy(f"{app}:{self.url_name}", kwargs={"pk": self.object.pk})


class UpdateViewMixin(
    ObjectUrlMixin, FormKwargsMixin, GetQuerysetMixin, CreateUpdateMixin, UpdateView
):
    template_name = "core/generic_form.html"
    form_action = "update"
    url_name = "update"


class DeleteViewMixin(
    ObjectUrlMixin, FormKwargsMixin, GetQuerysetMixin, DeleteMixin, DeleteView
):
    template_name = "core/generic_delete_form.html"
    url_name = "delete"


class RedirectViewMixin(RedirectView):
    pass


class TemplateViewMixin(TemplateView):
    pass


class ListViewMixin(GetQuerysetMixin, ListView):
    pass


class LoadToAccountViewMixin(ListViewMixin):
    """A move form's to_account options: the service's items but the from_account."""

    template_name = "core/dropdown.html"

    def get(self, request, *args, **kwargs):
        pk = int_or_zero(request.GET.get("from_account"))
        if not pk:
            return self.render_to_response({"object_list": []})

        items = self.service_class(request.user).items().exclude(pk=pk)
        return self.render_to_response({"object_list": items})


class FormViewMixin(FormKwargsMixin, FormView):
    template_name = "core/generic_form.html"


class SearchViewMixin(FormKwargsMixin, SearchMixin, TemplateView):
    pass
