from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.generic import CreateView, ListView, UpdateView

from ..mixins.ajax import AjaxCreateUpdateMixin
from .get import GetFormKwargs, GetQueryset
from .helpers import update_context


class ListMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, ListView):
    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_to_string(request)

        return super().dispatch(request, *args, **kwargs)

    def _render_to_string(self, request):
        return (
            render_to_string(
                self.template_name,
                {self.context_object_name: self.get_queryset()},
                request
            )
        )


class CreateMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'create')

        return context


class CreateAjaxMixin(AjaxCreateUpdateMixin, CreateMixin):
    pass


class UpdateMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'update')

        return context


class UpdateAjaxMixin(AjaxCreateUpdateMixin, UpdateMixin):
    pass
