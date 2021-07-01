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
            context = self.get_context_data(**{'no_items': True}) # calls GetQuerysetMixin get_context_data
            json_data = self._render_form(context=context)

            return JsonResponse(json_data)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.form_class(request.POST, request.FILES)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        context = {}
        json_data = {}

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

        if utils.is_ajax(self.request):
            json_data = self._render_form(context, json_data)
            return JsonResponse(json_data)

        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data(**{'no_items': True})
        context['form'] = form

        if utils.is_ajax(self.request):
            json_data = {'form_is_valid': False}
            json_data = self._render_form(context, json_data)
            return JsonResponse(json_data)

        return super().form_invalid(form)

    def _render_form(self, context, json_data=None):
        json_data = json_data if json_data else {}
        json_data.update({
            'html_form' : render_to_string(
                template_name=self.get_template_names(),
                context=context,
                request=self.request)
        })

        return json_data


class AjaxDeleteMixin(GetQuerysetMixin):
    list_render_output = True  # can turn-off render list
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

            if self.list_render_output:
                context = self.get_context_data()
                json_data['html_list'] = (
                    render_to_string(
                        self.get_list_template_name(), context, self.request)
                )
            else:
                context = self.get_context_data(**{'no_items': True})

            return JsonResponse(json_data)

        return self.delete(*args, **kwargs)


class AjaxCustomFormMixin(LoginRequiredMixin, FormView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        json_data = {
            'html_form': self._render_form(context),
            'html': None,
        }
        return JsonResponse(json_data)

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
            **kwargs,
        }
        return JsonResponse(json_data)

    def _render_form(self, context):
        if hasattr(self, 'url'):
            context.update({'url': self.url})

        return (
            render_to_string(self.template_name, context, request=self.request)
        )


class AjaxSearchMixin(AjaxCustomFormMixin):
    def post(self, request, *args, **kwargs):
        err = {'error': 'Form is broken.'}
        try:
            form_data = request.POST['form_data']
        except KeyError:
            return JsonResponse(data=err, status=404)

        try:
            _list = json.loads(form_data)

            # flatten list of dictionaries - form_data_list
            for field in _list:
                self.form_data_dict[field["name"]] = field["value"]

        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(data=err, status=500)

        form = self.form_class(self.form_data_dict)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form, **kwargs)
