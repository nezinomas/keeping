from django.core.exceptions import ImproperlyConfigured


class GetQuerysetMixin:
    service_class = None

    def get_queryset(self):
        if self.service_class is None:
            raise ImproperlyConfigured(
                f"[{self.__class__.__module__}.{self.__class__.__name__}] is missing a data source. "  # noqa: E501
                f"Please define the correct model service class in 'service_class' "
            )

        service = self.service_class(self.request.user)

        return service.objects
