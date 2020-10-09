import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic.edit import FormView

from ...core.lib import utils
from . import helpers as H
from .get import GetQuerysetMixin


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
        self.object = self.get_object()

        if utils.is_ajax(self.request):
            json_data = dict()
            context = self.get_context_data(**{'no_items': True}) # calls GetQuerysetMixin get_context_data
            self._render_form(json_data, context)

            return JsonResponse(json_data)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        json_data = dict()
        context = {}

        if form.is_valid():
            form.save()

            if self.list_render_output:
                context = self.get_context_data()
                json_data['html_list'] = (
                    render_to_string(
                        self.get_list_template_name(), context, self.request)
                )
            else:
                context = self.get_context_data(**{'no_items': True})

            context['form'] = form
            json_data['form_is_valid'] = True

        self._render_form(json_data, context)

        if utils.is_ajax(self.request):
            return JsonResponse(json_data)

        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data(**{'no_items': True})

        context['form'] = form
        json_data = {'form_is_valid': False}

        if utils.is_ajax(self.request):
            self._render_form(json_data, context)
            return JsonResponse(json_data)

        return super().form_invalid(form)

    def _render_form(self, json_data, context):
        json_data['html_form'] = (
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
            json_data = dict()
            context = self.get_context_data(**{'no_items': True})
            rendered = render_to_string(template_name=self.get_template_names(),
                                        context=context,
                                        request=request)

            json_data['html_form'] = rendered

            return JsonResponse(json_data)

        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        if utils.is_ajax(self.request):
            self.object = self.get_object()
            self.object.delete()

            json_data = dict()
            json_data['form_is_valid'] = True
            context = self.get_context_data()

            json_data['html_list'] = (
                render_to_string(
                    self.get_list_template_name(), context, self.request)
            )

            return JsonResponse(json_data)

        return self.delete(*args, **kwargs)


class AjaxCustomFormMixin(LoginRequiredMixin, FormView):
    def post(self, request, *args, **kwargs):
        err = {'error': 'Form is broken.'}
        try:
            form_data = request.POST['form_data']
        except KeyError:
            return JsonResponse(json_data=err, status=404)

        try:
            _list = json.loads(form_data)

            # flatten list of dictionaries - form_data_list
            for field in _list:
                self.form_data_dict[field["name"]] = field["value"]

        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(json_data=err, status=500)

        form = self.form_class(self.form_data_dict)
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form, **kwargs)

    def form_invalid(self, form):
        json_data = {
            'form_is_valid': False,
            'html_form': self._render_form({'form': form}),
            'html': None,
        }
        return JsonResponse(json_data)

    def form_valid(self, form, **kwargs):
        html = kwargs.get('html')
        html = html if html else 'Nieko neradau'

        json_data = {
            'form_is_valid': True,
            'html_form': self._render_form({'form': form}),
            'html': html,
        }
        return JsonResponse(json_data)

    def _render_form(self, context):
        if hasattr(self, 'url'):
            context.update({'url': self.url})

        return (
            render_to_string(self.template_name, context, request=self.request)
        )
