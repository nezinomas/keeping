from abc import ABC, abstractmethod

from django.shortcuts import reverse


def format_plural(verbose_name):
    plural = verbose_name + 's'

    if ' ' in verbose_name:
        _a = verbose_name.split(' ')
        _a[0] = _a[0] + 's'

        plural = '_'.join(_a)

    return plural


def app_name(obj: object):
    return obj.request.resolver_match.app_name


def model_plural_name(obj: object):
    return format_plural(obj.model._meta.verbose_name)


def template_name(obj: object, name: str) -> str:
    app = app_name(obj)
    model = model_plural_name(obj)

    return f'{app}/includes/{model}_{name}.html'


class UpdateContextAbstract(ABC):
    @abstractmethod
    def update_context(self, obj, context):
        pass


class UpdateAction(UpdateContextAbstract):
    @classmethod
    def update_context(cls, obj, context):
        app = app_name(obj)
        model = model_plural_name(obj)

        context['action'] = 'update'
        context['url'] = (
            reverse(
                f'{app}:{model}_update',
                kwargs={'pk': obj.object.pk}
            )
        )


class CreateAction(UpdateContextAbstract):
    @classmethod
    def update_context(cls, obj, context):
        app = app_name(obj)
        model = model_plural_name(obj)

        context['action'] = 'insert'
        context['url'] = reverse(f'{app}:{model}_new')


class DeleteAction(UpdateContextAbstract):
    @classmethod
    def update_context(cls, obj, context):
        app = app_name(obj)
        model = model_plural_name(obj)
        pk = obj.object.pk

        if pk:
            context['action'] = 'delete'
            context['url'] = reverse(f'{app}:{model}_delete', kwargs={'pk': pk})
