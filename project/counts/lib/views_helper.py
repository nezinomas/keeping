import contextlib

from ..models import CountType


class CountTypetObjectMixin():
    object = None

    def get_object(self):
        self.object = self.kwargs.get('object')

        if self.object:
            return

        if count_type_slug := self.kwargs.get('slug'):
            with contextlib.suppress(CountType.DoesNotExist):
                self.object = \
                        CountType.objects \
                        .related() \
                        .get(slug=count_type_slug)

                # push self.object to self.kwargs
                self.kwargs['object'] = self.object
