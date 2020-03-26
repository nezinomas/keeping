from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)

from .ajax import AjaxCreateUpdateMixin, AjaxDeleteMixin
from .get import GetQuerysetMixin
from .helpers import CreateAction, DeleteAction, UpdateAction, template_name


class IndexMixin(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if self.template_name is None:
            app_name = self.request.resolver_match.app_name
            return [f'{app_name}/index.html']

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
            return [template_name(self, 'list')]

        return [self.template_name]


class CreateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        CreateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        CreateAction.update_context(self, context)

        return context


class UpdateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        UpdateAction.update_context(self, context)

        return context


class DeleteAjaxMixin(
        LoginRequiredMixin,
        AjaxDeleteMixin,
        DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        DeleteAction.update_context(self, context)

        return context
