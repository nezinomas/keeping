from django.http import JsonResponse
from django.template.loader import render_to_string

from . import helpers as H
from .get import GetQuerysetMixin
from ...core.lib import utils


class AjaxCreateUpdateMixin(GetQuerysetMixin):
    list_template_name = None
    list_render_output = True  # can turn-off render list
    object = None

    def get_template_names(self):
        if self.template_name is None:
            return [H.template_name(self, 'form')]

        return [self.template_name]

    def get_list_template_name(self):
        if not self.list_template_name:
            return H.template_name(self, 'list')

        return self.list_template_name

    def get(self, request, *args, **kwargs):
        if 'pk' in self.kwargs:
            self.object = self.model.objects.get(pk=self.kwargs['pk'])

        if utils.is_ajax(self.request):
            data = dict()
            context = self.get_context_data() # calls GetQuerysetMixin get_context_data
            self._render_form(data, context)

            return JsonResponse(data)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        data = dict()
        context = {}

        if form.is_valid():
            form.save()

            context = self.get_context_data()
            context['form'] = form

            data['form_is_valid'] = True

            if self.list_render_output:
                data['html_list'] = (
                    render_to_string(
                        self.get_list_template_name(), context, self.request)
                )

        self._render_form(data, context)

        if utils.is_ajax(self.request):
            return JsonResponse(data)

        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data()

        context['form'] = form
        data = {'form_is_valid': False}

        if utils.is_ajax(self.request):
            self._render_form(data, context)
            return JsonResponse(data)

        return super().form_invalid(form)

    def _render_form(self, data, context):
        data['html_form'] = (
            render_to_string(self.get_template_names(),
                             context, request=self.request)
        )


class AjaxDeleteMixin(GetQuerysetMixin):
    list_template_name = None
    object = None

    def get_template_names(self):
        if self.template_name is None:
            return [H.template_name(self, 'delete_form')]

        return [self.template_name]

    def get_list_template_name(self):
        if not self.list_template_name:
            return H.template_name(self, 'list')

        return self.list_template_name

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if utils.is_ajax(self.request):
            data = dict()
            context = self.get_context_data()
            rendered = render_to_string(template_name=self.get_template_names(),
                                        context=context,
                                        request=request)

            data['html_form'] = rendered

            return JsonResponse(data)

        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        if utils.is_ajax(self.request):
            self.object = self.get_object()
            self.object.delete()

            data = dict()
            data['form_is_valid'] = True
            context = self.get_context_data()

            data['html_list'] = (
                render_to_string(
                    self.get_list_template_name(), context, self.request)
            )

            return JsonResponse(data)

        return self.delete(*args, **kwargs)
