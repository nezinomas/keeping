from abc import ABC, abstractmethod

from django.shortcuts import reverse


def format_plural(verbose_name):
    plural = verbose_name + 's'

    if ' ' in verbose_name:
        _a = verbose_name.split(' ')
        _a[0] = _a[0] + 's'

        plural = '_'.join(_a)

    return plural


def template_name(self: object, name: str) -> str:
    app_name = self.request.resolver_match.app_name
    plural = format_plural(self.model._meta.verbose_name)

    return f'{app_name}/includes/{plural}_{name}.html'


class UpdateContextAbstract(ABC):
    def app_name(self, obj):
        return obj.request.resolver_match.app_name

    def model_plural_name(self, obj):
        return format_plural(obj.model._meta.verbose_name)

    @abstractmethod
    def update_context(self, obj, context):
        pass


class UpdateAction(UpdateContextAbstract):
    @classmethod
    def update_context(cls, obj, context):
        app = cls.app_name(cls, obj)
        model = cls.model_plural_name(cls, obj)

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
        app = cls.app_name(cls, obj)
        model = cls.model_plural_name(cls, obj)

        context['action'] = 'insert'
        context['url'] = reverse(f'{app}:{model}_new')


class DeleteAction(UpdateContextAbstract):
    @classmethod
    def update_context(cls, obj, context):
        app = cls.app_name(cls, obj)
        model = cls.model_plural_name(cls, obj)
        pk = obj.object.pk

        if pk:
            context['action'] = 'delete'
            context['url'] = reverse(f'{app}:{model}_delete', kwargs={'pk': pk})
