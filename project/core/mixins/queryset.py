from django.core.exceptions import ImproperlyConfigured

class GetQuerysetMixin:
    object = None

    def get_queryset(self):
        # 1. Protect against developer error (forgetting to set the model)
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing a model definition. "
                f"Define {self.__class__.__name__}.model."
            )

        return self.model.objects.related(self.request.user)