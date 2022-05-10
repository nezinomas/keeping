import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, ListView,
                                  RedirectView, TemplateView, UpdateView, FormView)
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event

from ...core.lib import search


def rendered_content(request, view_class, **kwargs):
    # update request kwargs
    request.resolver_match.kwargs.update({**kwargs})

    return (
        view_class
        .as_view()(request, **kwargs)
        .rendered_content
    )


class GetQuerysetMixin():
    def get_queryset(self):
        try:
            qs = self.model.objects.related()
        except AttributeError:
            raise Http404(
                _("No %(verbose_name)s found matching the query") % \
                {'verbose_name': self.model._meta.verbose_name})

        return qs


class SearchMixin(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({**self.search()})

        return context

    def get_search_method(self):
        return getattr(search, self.search_method)

    def search(self):
        search_str = self.request.GET.get('search')
        page = self.request.GET.get('page', 1)
        sql = self.get_search_method()(search_str)

        context = {
            'object_list': None,
            'notice': _('Found nothing'),
        }

        if sql:
            paginator = Paginator(sql, self.per_page)
            page_range = paginator.get_elided_page_range(number=page)

            app = self.request.resolver_match.app_name

            context.update({
                'object_list': paginator.get_page(page),
                'search': search_str,
                'url': reverse(f"{app}:search"),
                'page_range': page_range,
            })
        return context


class CreateUpdateMixin():
    hx_trigger = 'reload'
    hx_redirect = None

    def get_hx_trigger(self):
        return self.hx_trigger

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_action': self.form_action,
            'url': self.url,
        })
        return context

    def form_valid(self, form, **kwargs):
        response = super().form_valid(form)

        if self.request.htmx:
            self.hx_redirect = self.get_hx_redirect()
            if self.hx_redirect:
                # close form and redirect to url with hx_trigger
                return HttpResponseClientRedirect(self.hx_redirect)

            # close form and reload container
            response.status_code = 204
            trigger_client_event(
                response,
                self.get_hx_trigger(),
                {},
            )
            return response

        return response


class CreateViewMixin(LoginRequiredMixin,
                      GetQuerysetMixin,
                      CreateUpdateMixin,
                      CreateView):
    form_action = 'insert'

    def url(self):
        app = self.request.resolver_match.app_name
        return reverse_lazy(f'{app}:new')


class UpdateViewMixin(LoginRequiredMixin,
                      GetQuerysetMixin,
                      CreateUpdateMixin,
                      UpdateView):
    form_action = 'update'

    def url(self):
        if self.object:
            return self.object.get_absolute_url()
        return None


class DeleteViewMixin(LoginRequiredMixin,
                      GetQuerysetMixin,
                      DeleteView):
    hx_trigger = 'reload'
    hx_redirect = None

    def get_hx_trigger(self):
        return self.hx_trigger

    def get_hx_redirect(self):
        return self.hx_redirect

    def url(self):
        if self.object:
            return self.object.get_delete_url()
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'url': self.url,
        })
        return context

    def post(self, *args, **kwargs):
        if self.get_object():
            super().post(*args, **kwargs)

            hx_redirect = self.get_hx_redirect()
            if hx_redirect:
                return HttpResponseClientRedirect(hx_redirect)
            else:
                return HttpResponse(
                    status=204,
                    headers={
                        'HX-Trigger': json.dumps({self.get_hx_trigger(): None}),
                    },
                )
        return HttpResponse()


class RedirectViewMixin(LoginRequiredMixin, RedirectView):
    pass


class TemplateViewMixin(LoginRequiredMixin,
                        TemplateView):
    pass


class ListViewMixin(LoginRequiredMixin,
                    GetQuerysetMixin,
                    ListView):
    pass


class FormViewMixin(LoginRequiredMixin,
                    FormView):
    pass


class ListMixin(ListView):
    # TODO: delete this class
    pass


class IndexMixin(TemplateView):
    # TODO: delete this class
    pass


class CreateAjaxMixin(CreateView):
    # TODO: delete this class
    pass


class UpdateAjaxMixin(UpdateView):
    # TODO: delete this class
    pass


class DeleteAjaxMixin(DeleteView):
    # TODO: delete this class
    pass


class DispatchAjaxMixin():
    # TODO: delete this class
    pass


class DispatchListsMixin():
    # TODO: delete this class
    pass
