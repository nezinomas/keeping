from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)

from . import helpers as H
from .ajax import AjaxCreateUpdateMixin, AjaxDeleteMixin
from .get import GetQuerysetMixin


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

    def get_context_data(self, **kwargs):
        app = H.app_name(self)
        model = H.model_plural_name(self)

        context = super().get_context_data(**kwargs)
        context['action'] = _('insert')
        context['url'] = reverse(f'{app}:{model}_new')

        return context


class UpdateAjaxMixin(
        LoginRequiredMixin,
        AjaxCreateUpdateMixin,
        UpdateView):

    def get_context_data(self, **kwargs):
        # app = H.app_name(self)
        # model = H.model_plural_name(self)

        context = super().get_context_data(**kwargs)
        context.update({
            'action': _('update'),
            # 'url': reverse(f'{app}:{model}_update', kwargs={'pk': self.object.pk}),
        })

        return context


class DeleteAjaxMixin(
        LoginRequiredMixin,
        AjaxDeleteMixin,
        DeleteView):

    def get_context_data(self, **kwargs):
        # app = H.app_name(self)
        # model = H.model_plural_name(self)
        pk = self.object.pk

        context = super().get_context_data(**kwargs)

        if pk:
            context.update({
                'action': 'delete',
                # 'url': reverse(f'{app}:{model}_delete', kwargs={'pk': pk}),
            })

        return context


class DispatchAjaxMixin():
    def dispatch(self, request, *args, **kwargs):
        try:
            request.GET['ajax_trigger']
        except KeyError:
            return redirect(reverse(self.redirect_view))

        return super().dispatch(request, *args, **kwargs)
