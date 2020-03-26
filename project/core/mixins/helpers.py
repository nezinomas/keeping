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
