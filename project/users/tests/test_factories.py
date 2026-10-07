import pytest
from django.test import override_settings

from ...journals.tests.factories import JournalFactory
from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_factory_journal_takes_the_site_language():
    user = UserFactory(username="fresh", email="fresh@fresh.com")

    assert user.journal.lang == "lt"


@override_settings(LANGUAGE_CODE="en")
def test_user_factory_journal_reads_language_code():
    user = UserFactory(username="fresh", email="fresh@fresh.com")

    assert user.journal.lang == "en"


@override_settings(LANGUAGE_CODE="en")
def test_journal_factory_reads_language_code():
    assert JournalFactory.build().lang == "en"


def test_user_factory_keeps_the_language_of_a_passed_journal():
    journal = JournalFactory(title="Other Journal", lang="en")

    user = UserFactory(username="fresh", email="fresh@fresh.com", journal=journal)

    journal.refresh_from_db()
    assert user.journal.lang == "en"
    assert journal.lang == "en"
