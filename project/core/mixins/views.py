import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)
from django_htmx.http import trigger_client_event

from ...core.lib import search
from .get import GetQuerysetMixin


class DispatchMixin():
    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            rendered = render_to_string(
                template_name=self.get_template_names(),
                context=self.get_context_data(),
                request=request
            )
            return rendered

        return super().dispatch(request, *args, **kwargs)


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

    def get_hx_trigger(self):
        return self.hx_trigger

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
            response.status_code = 204
            trigger_client_event(
                response,
                self.get_hx_trigger(),
                {},
            )
        return response


class CreateViewMixin(LoginRequiredMixin,
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

    def get_hx_trigger(self):
        return self.hx_trigger

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

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({self.get_hx_trigger(): None}),
                },
            )
        return HttpResponse()


class TemplateViewMixin(LoginRequiredMixin,
                        DispatchMixin,
                        TemplateView):
    pass


class ListViewMixin(LoginRequiredMixin,
                    DispatchMixin,
                    GetQuerysetMixin,
                    ListView):
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
