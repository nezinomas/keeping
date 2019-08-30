from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .ajax import AjaxCreateUpdateMixin
from .get import GetFormKwargs, GetQueryset
from .helpers import format_url_name, update_context


class IndexMixin(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if self.template_name is None:
            app_name = self.request.resolver_match.app_name
            return [f'{app_name}/index.html']
        else:
            return [self.template_name]


class ListMixin(
        LoginRequiredMixin,
        GetQueryset, GetFormKwargs,
        ListView):

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_to_string(request)

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.template_name is None:
            plural = format_url_name(self.model._meta.verbose_name)
            app_name = self.request.resolver_match.app_name
            return [f'{app_name}/includes/{plural}_list.html']
        else:
            return [self.template_name]

    def _render_to_string(self, request):
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
        AjaxCreateUpdateMixin, GetQueryset, GetFormKwargs,
        CreateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'create')

        return context


class UpdateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin, GetQueryset, GetFormKwargs,
        UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'update')

        return context
