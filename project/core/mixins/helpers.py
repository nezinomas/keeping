from django.shortcuts import reverse


def format_url_name(verbose_name):
    plural = verbose_name + 's'

    if ' ' in verbose_name:
        _a = verbose_name.split(' ')
        _a[0] = _a[0] + 's'

        plural = '_'.join(_a)

    return plural


def template_name(self: object, name: str) -> str:
    app_name = self.request.resolver_match.app_name
    plural = format_url_name(self.model._meta.verbose_name)

    return f'{app_name}/includes/{plural}_{name}.html'


def update_context(self, context, action):
        plural = format_url_name(self.model._meta.verbose_name)
        app_name = self.request.resolver_match.app_name

        if action is 'update':
            context['action'] = 'update'
            context['url'] = (
                reverse(
                    f'{app_name}:{plural}_update',
                    kwargs={'pk': self.object.pk}
                )
            )

        if action is 'create':
            context['action'] = 'insert'
            context['url'] = reverse(f'{app_name}:{plural}_new')
