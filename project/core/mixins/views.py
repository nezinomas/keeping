import json

from django.core.exceptions import FieldError
from django.db.models import Count, F, Sum
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
from ..lib.paginator import CountlessPaginator


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
            "modal_form_title": getattr(self, "modal_form_title", None),
            "modal_body_css_class": getattr(self, "modal_body_css_class", ""),
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

        if self.search_method not in ["search_expenses"]:
            return {}

        try:
            q = (
                sql.annotate(count=Count("id"))
                .values("count")
                .annotate(
                    sum_price=Sum("price"),
                    sum_quantity=Sum("quantity"),
                )
                .order_by("count")
                .values(
                    "count",
                    "sum_price",
                    "sum_quantity",
                    average=F("sum_price") / F("sum_quantity"),
                )
            )
        except (AttributeError, FieldError):
            return {}

        return q[0] if q else {}

    def search(self):
        search_str = self.request.GET.get("search")

        sql = self.get_search_method()(search_str)
        stats = self.search_statistic(sql)

        page = self.request.GET.get("page", 1)
        paginator = CountlessPaginator(
            query=sql, total_records=stats.get("count", 0), per_page=self.per_page
        )
        page_range = paginator.get_elided_page_range(page)

        app = self.request.resolver_match.app_name

        return {
            "notice": _("No data found"),
            "object_list": paginator.get_page(page),
            "search": search_str,
            "url": reverse(f"{app}:search"),
            "paginator_object": {
                "total_pages": paginator.total_pages,
                "page_range": page_range,
                "ELLIPSIS": paginator.ELLIPSIS,
            },
            **stats,
        }


# -------------------------------------------------------------------------------------
#                                                                          Views Mixins
# -------------------------------------------------------------------------------------
class CreateViewMixin(GetQuerysetMixin, CreateUpdateMixin, CreateView):
    template_name = "core/generic_form.html"
    form_action = "insert"

    def url(self):
        app = self.request.resolver_match.app_name
        return reverse_lazy(f"{app}:new")


class UpdateViewMixin(GetQuerysetMixin, CreateUpdateMixin, UpdateView):
    template_name = "core/generic_form.html"
    form_action = "update"

    def url(self):
        return self.object.get_absolute_url() if self.object else None


class DeleteViewMixin(GetQuerysetMixin, DeleteMixin, DeleteView):
    template_name = "core/generic_delete_form.html"


class RedirectViewMixin(RedirectView):
    pass


class TemplateViewMixin(TemplateView):
    pass


class ListViewMixin(GetQuerysetMixin, ListView):
    pass


class FormViewMixin(FormView):
    template_name = "core/generic_form.html"


class SearchViewMixin(SearchMixin, TemplateView):
    pass
