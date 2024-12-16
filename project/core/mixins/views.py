import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event
from vanilla import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from ...core.lib import search


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
class GetQuerysetMixin:
    object = None

    def get_queryset(self):
        try:
            qs = self.model.objects.related()
        except AttributeError as e:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": self.model._meta.verbose_name}
            ) from e

        return qs


class CreateUpdateMixin:
    hx_trigger_django = None
    hx_trigger_form = None
    hx_redirect = None

    def get_hx_trigger_django(self):
        # triggers Htmx to reload container on Submit button click
        # triggering happens many times
        return self.hx_trigger_django or None

    def get_hx_trigger_form(self):
        # triggers Htmx to reload container on Close button click
        # triggering happens once
        return self.hx_trigger_form or None

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = {
            "form_title": getattr(self, "form_title", None),
            "form_action": self.form_action,
            "url": self.url,
            "hx_trigger_form": self.get_hx_trigger_form(),
        }
        return super().get_context_data(**kwargs) | context

    def form_valid(self, form, **kwargs):
        response = super().form_valid(form)

        if not self.request.htmx:
            return response

        self.hx_redirect = self.get_hx_redirect()

        if self.hx_redirect:
            # close form and redirect to url with hx_trigger_django
            return HttpResponseClientRedirect(self.hx_redirect)

        # close form and reload container
        response.status_code = 204
        if trigger := self.get_hx_trigger_django():
            trigger_client_event(response=response, name=trigger, params={})
        return response


class DeleteMixin:
    hx_trigger_django = "reload"
    hx_redirect = None

    def get_hx_trigger_django(self):
        return self.hx_trigger_django

    def get_hx_redirect(self):
        return self.hx_redirect

    def url(self):
        return self.object.get_delete_url() if self.object else None

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"url": self.url}

    def post(self, *args, **kwargs):
        super().post(*args, **kwargs)

        if hx_redirect := self.get_hx_redirect():
            return HttpResponseClientRedirect(hx_redirect)

        return http_htmx_response(self.get_hx_trigger_django())


class SearchMixin:
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | self.search()

    def get_search_method(self):
        return getattr(search, self.search_method)

    def search_statistic(self, sql):
        """
        Calculate total price, total quantity and average of search result.

        :param sql: QuerySet
        :return:
            a dictionary with sum_price, sum_quantity and average
            if search_method is 'search_expenses'
        :rtype: dict or None
        """
        return (
            sql.aggregate(
                sum_price=Sum("price"),
                sum_quantity=Sum("quantity"),
                average=Sum("price") / Sum("quantity"),
            )
            if sql and self.search_method in ["search_expenses"]
            else {}
        )

    def search(self):
        search_str = self.request.GET.get("search")

        sql = self.get_search_method()(search_str)

        page = self.request.GET.get("page", 1)
        paginator = Paginator(sql, self.per_page)
        page_range = paginator.get_elided_page_range(number=page)

        app = self.request.resolver_match.app_name

        return {
            "notice": _("No data found"),
            "object_list": paginator.get_page(page),
            "first_item": paginator.count - (paginator.per_page * (int(page) - 1)),
            "search": search_str,
            "url": reverse(f"{app}:search"),
            "page_range": page_range,
            **self.search_statistic(sql),
        }


# -------------------------------------------------------------------------------------
#                                                                          Views Mixins
# -------------------------------------------------------------------------------------
class CreateViewMixin(
    LoginRequiredMixin, GetQuerysetMixin, CreateUpdateMixin, CreateView
):
    form_action = "insert"

    def url(self):
        app = self.request.resolver_match.app_name
        return reverse_lazy(f"{app}:new")


class UpdateViewMixin(
    LoginRequiredMixin, GetQuerysetMixin, CreateUpdateMixin, UpdateView
):
    form_action = "update"

    def url(self):
        return self.object.get_absolute_url() if self.object else None


class DeleteViewMixin(LoginRequiredMixin, GetQuerysetMixin, DeleteMixin, DeleteView):
    pass


class RedirectViewMixin(LoginRequiredMixin, RedirectView):
    pass


class TemplateViewMixin(LoginRequiredMixin, TemplateView):
    pass


class ListViewMixin(LoginRequiredMixin, GetQuerysetMixin, ListView):
    pass


class FormViewMixin(LoginRequiredMixin, FormView):
    pass


class SearchViewMixin(LoginRequiredMixin, SearchMixin, TemplateView):
    pass
