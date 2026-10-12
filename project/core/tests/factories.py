import factory
from django.db import models as django_models

from .. import models


class TitleDummy(models.TitleAbstract):
    pass


class TitleDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TitleDummy

    title = "Title"


class OwnedTitleDummy(models.TitleAbstract):
    owner = django_models.ForeignKey(TitleDummy, on_delete=django_models.CASCADE)

    class Meta:
        constraints = [
            django_models.UniqueConstraint(
                fields=["owner", "slug"], name="owned_title_dummy_owner_slug"
            )
        ]


class OwnedTitleDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OwnedTitleDummy

    owner = factory.SubFactory(TitleDummyFactory)
    title = "Title"
