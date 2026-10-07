import copy
import importlib
import sys

import pytest
from django.template.backends.django import DjangoTemplates

from ...config.settings import base

PRODUCTION = "project.config.settings.production"


@pytest.fixture
def import_production():
    def _import():
        sys.modules.pop(PRODUCTION, None)
        return importlib.import_module(PRODUCTION)

    yield _import
    sys.modules.pop(PRODUCTION, None)


def test_importing_production_leaves_base_templates_alone(import_production):
    before = copy.deepcopy(base.TEMPLATES)

    import_production()

    assert base.TEMPLATES == before


def test_production_templates_cache_the_loaders(import_production):
    expected = copy.deepcopy(base.TEMPLATES)
    expected[0]["APP_DIRS"] = False
    expected[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

    assert import_production().TEMPLATES == expected


def test_production_templates_build_an_engine(import_production):
    params = {**import_production().TEMPLATES[0], "NAME": "production"}
    del params["BACKEND"]

    DjangoTemplates(params)
