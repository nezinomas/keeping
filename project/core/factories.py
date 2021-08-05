import factory

from . import models


class TitleDummy(models.TitleAbstract):
    pass


class TitleDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TitleDummy

    title = 'Title'
