from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string


class CrudMixinSettings(object):
    def __init__(self, *args, **kwargs):
        self._model = None

        self._form = None
        self._form_template = 'form_template.html'

        self._item_id = None

        self._items_template = 'items_template.html'
        self._items_template_main = 'items_main_template.html'
        self._items_template_var_name = 'items'

        self._url_new = None
        self._url_update = None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, value):
        self._form = value

    @property
    def form_template(self):
        return self._form_template

    @form_template.setter
    def form_template(self, value):
        self._form_template = value

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, value):
        self._item_id = value

    @property
    def items_template(self):
        return self._items_template

    @items_template.setter
    def items_template(self, value):
        self._items_template = value

    @property
    def items_template_main(self):
        return self._items_template_main

    @items_template_main.setter
    def items_template_main(self, value):
        self._items_template_main = value

    @property
    def items_template_var_name(self):
        return self._items_template_var_name

    @items_template_var_name.setter
    def items_template_var_name(self, value):
        self._items_template_var_name = value

    @property
    def url_new(self):
        return self._url_new

    @url_new.setter
    def url_new(self, value):
        self._url_new = value

    @property
    def url_update(self):
        return self._url_update

    @url_update.setter
    def url_update(self, value):
        self._url_update = value


class CrudMixin(object):
    def __init__(self, request, settings, *args, **kwargs):
        self._request = request
        self._settings = settings

        self._items = None
        self._data = {}

        if not self._settings.model or not self._settings.form:
            raise AttributeError(
                'Oh no! No model_name or form_name in CrudMixinSettings!'
            )

        self._get_items()

    def _get_items(self):
        try:
            self._items = (
                self._settings.model.objects.items(
                    **{'year': self._request.user.profile.year}
                )
            )
        except Exception as ex:
            self._items = self._settings.model.objects.all()

    def _update_data(self):
        self._data.update({
            'form_is_valid': True,
            'html_list': render_to_string(
                self._settings.items_template,
                {self._settings.items_template_var_name: self._items}
            )
        })

    def _json_response(self, context, form):
        if self._request.method == 'POST':
            if form.is_valid():
                form.save()
                self._update_data()
            else:
                self._data['form_is_valid'] = False

        self._data.update({
            'html_form': render_to_string(
                self._settings.form_template,
                context,
                self._request
            )
        })

        return JsonResponse(self._data)

    def lists_as_str(self):
        return render_to_string(
            self._settings.items_template,
            {self._settings.items_template_var_name: self._items},
            self._request,
        )

    def lists_as_html(self, context={}):
        form = self._settings.form()
        context.update({
            self._settings.items_template_var_name: self._items,
            'form': form
        })

        return render(
            self._request,
            self._settings.items_template_main,
            context=context
        )

    def new(self):
        form = self._settings.form(self._request.POST or None)
        context = {
            'url': reverse(self._settings.url_new),
            'action': 'insert',
            'form': form
        }

        return self._json_response(context, form)

    def update(self):
        object = get_object_or_404(self._settings.model, pk=self._settings.item_id)
        form = self._settings.form(self._request.POST or None, instance=object)
        url = reverse(
            self._settings.url_update,
            kwargs={'pk': self._settings.item_id}
        )
        context = {'url': url, 'action': 'update', 'form': form}

        return self._json_response(context, form)
