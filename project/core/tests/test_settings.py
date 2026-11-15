import copy
import importlib
import sys

import pytest
from django.core.checks.security.base import check_csp_nonce_context_processor
from django.template.backends.django import DjangoTemplates
from django.test import override_settings

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


def test_production_templates_build_an_engine_that_caches(import_production):
    params = {**import_production().TEMPLATES[0], "NAME": "production"}
    del params["BACKEND"]

    engine = DjangoTemplates(params)

    first, again = (engine.get_template("empty.html").template for _ in range(2))

    assert first is again


def test_production_csp_nonce_reaches_the_templates(import_production):
    production = import_production()

    with override_settings(
        MIDDLEWARE=production.MIDDLEWARE,
        SECURE_CSP=production.SECURE_CSP,
        TEMPLATES=production.TEMPLATES,
    ):
        assert check_csp_nonce_context_processor(None) == []
