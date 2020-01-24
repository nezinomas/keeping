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


def update_context(self, context, action):
    plural = format_plural(self.model._meta.verbose_name)
    app_name = self.request.resolver_match.app_name

    if action == 'update':
        context['action'] = 'update'
        context['url'] = (
            reverse(
                f'{app_name}:{plural}_update',
                kwargs={'pk': self.object.pk}
            )
        )

    if action == 'create':
        context['action'] = 'insert'
        context['url'] = reverse(f'{app_name}:{plural}_new')

    if action == 'delete' and self.object.pk:
        context['action'] = 'delete'
        context['url'] = reverse(f'{app_name}:{plural}_delete',
                                 kwargs={'pk': self.object.pk})
