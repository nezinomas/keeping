import json

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_htmx.http import HttpResponseClientRedirect
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
from .search import SearchMixin


def rendered_content(request, view_class, **kwargs):
    # update request kwargs
    request.resolver_match.kwargs.update({**kwargs})

    return view_class.as_view()(request, **kwargs).rendered_content


def http_htmx_response(hx_trigger_name=None, status_code=204):
    headers = {}
    if hx_trigger_name:
        headers = {
            "HX-Trigger": json.dumps({hx_trigger_name: None}),
        }

    return HttpResponse(
        status=status_code,
        headers=headers,
    )


# -------------------------------------------------------------------------------------
#                                                                                Mixins
# -------------------------------------------------------------------------------------
class AddUserToKwargsMixin:
    def get_form_kwargs(self, **kwargs):
        kwargs["user"] = self.request.user
        return kwargs

    def get_form(self, data=None, files=None, **kwargs):
        kwargs = self.get_form_kwargs(**kwargs)
        return self.form_class(data, files, **kwargs)

    def get_formset_class(self):
        # capture methods
        base_form = self.form_class
        get_kwargs = self.get_form_kwargs

        class UserAwareForm(base_form):
            def __init__(self, *args, **form_kwargs):
                form_kwargs = get_kwargs(**form_kwargs)  # using captured closure
                super().__init__(*args, **form_kwargs)

        return UserAwareForm


class GetQuerysetMixin:
    object = None

    def get_queryset(self):
        # 1. Protect against developer error (forgetting to set the model)
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing a model definition. "
                f"Define {self.__class__.__name__}.model."
            )

        return self.model.objects.related(self.request.user)


class DeleteMixin:
    hx_trigger_django = "reload"
    hx_redirect = None

    def get_hx_trigger_django(self):
        return self.hx_trigger_django

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = {
            "url": self.url,
            "modal_form_title": self.modal_form_title,
        }
        return super().get_context_data(**kwargs) | context

    def post(self, *args, **kwargs):
        super().post(*args, **kwargs)

        if hx_redirect := self.get_hx_redirect():
            return HttpResponseClientRedirect(hx_redirect)

        return http_htmx_response(self.get_hx_trigger_django())


# -------------------------------------------------------------------------------------
#                                                                          Views Mixins
# -------------------------------------------------------------------------------------
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
