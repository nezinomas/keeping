import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
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
        url = self._update_url()

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
        context['url'] = url
        json_data['form_is_valid'] = True

        if utils.is_ajax(self.request):
            json_data = self._render_form(context, json_data)
            return JsonResponse(json_data)

        return super().form_valid(form)

    def form_invalid(self, form):
        url = self._update_url()

        context = self.get_context_data(**{'no_items': True})
        context['form'] = form
        context['url'] = url

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

    def _update_url(self):
        # if object exists, generate update url
        # if there are errors in the form and no url
        # impossible to submit form data
        app = H.app_name(self)
        model = H.model_plural_name(self)
        new_view = f"{app}:{model}_new"
        update_view = f"{app}:{model}_update"

        # tweak for url resolver for
        # count_types in Counts
        # type in Debts, DebtsReturn
        _dict = {}
        if self.kwargs.get('count_type'):
            _dict['count_type'] = self.kwargs.get('count_type')

        if self.kwargs.get('type'):
            _dict['type'] = self.kwargs.get('count_type')

        if self.object:
            url = reverse(update_view, kwargs={"pk": self.object.pk, **_dict})
        else:
            url = reverse(new_view, kwargs={**_dict})

        return url


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

            if self.object:
                context = self.get_context_data(**{'no_items': True})
                template_name = self.get_template_names()
            else:
                context = {}
                template_name = 'empty_modal.html'

            rendered = render_to_string(template_name=template_name,
                                        context=context,
                                        request=request)

            json_data['html_form'] = rendered

            return JsonResponse(json_data)

        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        if utils.is_ajax(self.request):
            self.object = self.get_object()
            if self.object:
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
        context = self.get_context_data()
        context['form'] = form

        json_data = {
            'form_is_valid': False,
            'html_form': self._render_form(context),
            'html': None,
        }

        return JsonResponse(json_data)

    def form_valid(self, form, **kwargs):
        html = kwargs.get('html')

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

        if hasattr(self, 'update_container'):
            context.update({'update_container': self.update_container})

        return (
            render_to_string(self.template_name, context, request=self.request)
        )


class AjaxSearchMixin(AjaxCustomFormMixin):
    def make_form_data_dict(self):
        _list = json.loads(self.form_data)

        # flatten list of dictionaries - form_data_list
        for field in _list:
            self.form_data_dict[field["name"]] = field["value"]

    def post(self, request, *args, **kwargs):
        err = {'error': _('Form is broken.')}

        try:
            self.form_data = request.POST['form_data']
        except KeyError:
            return JsonResponse(data=err, status=404)

        try:
            self.make_form_data_dict()
        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(data=err, status=500)

        form = self.form_class(self.form_data_dict)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form, **kwargs)
