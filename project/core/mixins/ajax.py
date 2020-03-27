from django.http import JsonResponse
from django.template.loader import render_to_string

from .get import GetQuerysetMixin
from .helpers import template_name


class AjaxCreateUpdateMixin(GetQuerysetMixin):
    list_template_name = None
    list_render_output = True  # can turn-off render list
    object = None

    def get_template_names(self):
        if self.template_name is None:
            return [template_name(self, 'form')]

        return [self.template_name]

    def get(self, request, *args, **kwargs):
        if 'pk' in self.kwargs:
            self.object = self.get_object()

        if request.is_ajax():
            data = dict()
            context = self.get_context_data()
            self._render_form(data, context)

            return JsonResponse(data)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        data = dict()

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

        if self.request.is_ajax():
            return JsonResponse(data)

        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data()

        context['form'] = form
        data = {'form_is_valid': False}

        if self.request.is_ajax():
            self._render_form(data, context)
            return JsonResponse(data)

        return super().form_invalid(form)

    def _render_form(self, data, context):
        data['html_form'] = (
            render_to_string(self.get_template_names(),
                             context, request=self.request)
        )

    def get_list_template_name(self):
        if not self.list_template_name:
            return template_name(self, 'list')

        return self.list_template_name


class AjaxDeleteMixin(GetQuerysetMixin):
    list_template_name = None
    object = None

    def get_template_names(self):
        if self.template_name is None:
            return [template_name(self, 'delete_form')]

        return [self.template_name]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.is_ajax():
            data = dict()
            context = self.get_context_data()
            rendered = render_to_string(template_name=self.get_template_names(),
                                        context=context,
                                        request=request)

            data['html_form'] = rendered

            return JsonResponse(data)

        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        if self.request.is_ajax():
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

    def get_list_template_name(self):
        if not self.list_template_name:
            return template_name(self, 'list')

        return self.list_template_name
