import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)
from django_htmx.http import trigger_client_event
from requests import request

from ...core.lib import utils
from . import helpers as H
from .ajax import AjaxCreateUpdateMixin, AjaxDeleteMixin
from .get import GetQuerysetMixin


class CreateUpdateMixin():
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
                "reloadTrigger",
                {},
            )
            return response

        return response


class DeleteMixin():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'url': self.url,
        })

        return context

    def post(self, *args, **kwargs):
        super().post(*args, **kwargs)

        return HttpResponse(
            status=204,
            headers={
                'HX-Trigger': json.dumps({"reloadTrigger": None}),
            },
        )


class IndexMixin(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if self.template_name is None:
            app = H.app_name(self)
            return [f'{app}/index.html']

        return [self.template_name]


class ListMixin(
        LoginRequiredMixin,
        GetQuerysetMixin,
        ListView):

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            rendered = render_to_string(
                template_name=self.get_template_names(),
                context=self.get_context_data(),
                request=request
            )
            return rendered

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.template_name is None:
            return [H.template_name(self, 'list')]

        return [self.template_name]


class CreateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        CreateView):

    def dispatch(self, request, *args, **kwargs):
        if not utils.is_ajax(self.request):
            return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        app = H.app_name(self)
        model = H.model_plural_name(self)
        view_name = f'{app}:{model}_new'

        context = super().get_context_data(**kwargs)
        context['submit_button'] = _('Insert')
        context['form_action'] = 'insert'

        # tweak for url resolver for count types
        _dict = {}
        if self.kwargs.get('count_type'):
            _dict['count_type'] = self.kwargs.get('count_type')

        # tweak for url resolver for Debt types
        if self.kwargs.get('debt_type'):
            _dict['debt_type'] = self.kwargs.get('debt_type')

        context['url'] = reverse(view_name, kwargs={**_dict})

        return context


class UpdateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        UpdateView):

    def dispatch(self, request, *args, **kwargs):
        if not utils.is_ajax(self.request):
            return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # app = H.app_name(self)
        # model = H.model_plural_name(self)

        context = super().get_context_data(**kwargs)
        context.update({
            'submit_button': _('Update'),
            'form_action': 'update'
        })

        return context


class DeleteAjaxMixin(
        LoginRequiredMixin,
        AjaxDeleteMixin,
        DeleteView):

    def dispatch(self, request, *args, **kwargs):
        if not utils.is_ajax(self.request):
            return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # app = H.app_name(self)
        # model = H.model_plural_name(self)
        try:
            pk = self.object.pk
        except AttributeError:
            pk = None

        context = super().get_context_data(**kwargs)

        if pk:
            context.update({
                'submit_button': _('Delete'),
                'form_action': 'delete'
            })

        return context


class DispatchAjaxMixin():
    def dispatch(self, request, *args, **kwargs):
        try:
            request.GET['ajax_trigger']
        except KeyError:
            return redirect(self.redirect_view)

        return super().dispatch(request, *args, **kwargs)


class DispatchListsMixin():
    def dispatch(self, request, *args, **kwargs):
        if not utils.is_ajax(self.request):
            if 'as_string' not in kwargs and not self.request.user.is_anonymous:
                return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)
