import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)
from django_htmx.http import trigger_client_event

from .get import GetQuerysetMixin


class CreateUpdateMixin():
    hx_trigger = 'reload'

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
                self.hx_trigger,
                {},
            )
        return response


class TemplateViewMixin(LoginRequiredMixin,
                        TemplateView):
    pass


class ListViewMixin(LoginRequiredMixin,
                    GetQuerysetMixin,
                    ListView):
    pass


class CreateViewMixin(LoginRequiredMixin,
                      CreateUpdateMixin,
                      CreateView):
    form_action = 'insert'


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
                    'HX-Trigger': json.dumps({self.hx_trigger: None}),
                },
            )
        return HttpResponse()


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
