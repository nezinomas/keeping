from django.template.loader import render_to_string
from django.http import JsonResponse


class SaveDataMixin(object):
    def __init__(self, request, context, form):
        self.__data = {}
        self.__request = request
        self.__context = context
        self.__form = form
        self.__items_template_var_name = 'objects'

        self.__context.update({'form': form})

    @property
    def form_template(self):
        return self.__form_template

    @form_template.setter
    def form_template(self, value):
        self.__form_template = value

    @property
    def items_template(self):
        return self.__items_template

    @items_template.setter
    def items_template(self, value):
        self.__items_template = value

    @property
    def items(self):
        return self.__items

    @items.setter
    def items(self, value):
        self.__items = value

    @property
    def items_template_var_name(self):
        return self.__items_template_var_name

    @items_template_var_name.setter
    def items_template_var_name(self, value):
        self.__items_template_var_name = value

    def __update_data(self):
        self.__data.update({
            'form_is_valid': True,
            'html_list': render_to_string(
                self.__items_template,
                {self.__items_template_var_name: self.__items}
            )
        })

    def GenJsonResponse(self):
        if self.__request.method == 'POST':
            if self.__form.is_valid():
                self.__form.save()
                self.__update_data()
            else:
                self.__data['form_is_valid'] = False

        self.__data.update({
            'html_form': render_to_string(
                self.__form_template,
                self.__context,
                self.__request
            )
        })

        return JsonResponse(self.__data)
