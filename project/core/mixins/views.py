from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)

from .ajax import AjaxCreateUpdateMixin, AjaxDeleteMixin
from .get import GetQuerysetMixin
from .helpers import template_name, update_context


class IndexMixin(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if self.template_name is None:
            app_name = self.request.resolver_match.app_name
            return [f'{app_name}/index.html']
        else:
            return [self.template_name]


class ListMixin(
        LoginRequiredMixin,
        GetQuerysetMixin,
        ListView):

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_to_string(request, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.template_name is None:
            return [template_name(self, 'list')]

        return [self.template_name]

    def _render_to_string(self, request, **kwargs):
        template_name = self.get_template_names()

        return (
            render_to_string(
                template_name,
                {self.context_object_name: self.get_queryset()},
                request
            )
        )


class CreateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        CreateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'create')

        return context


class UpdateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'update')

        return context


class DeleteAjaxMixin(
        LoginRequiredMixin,
        AjaxDeleteMixin,
        DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        update_context(self, context, 'delete')

        return context
