import pytest
from django.core.exceptions import ValidationError

from .factories import JournalFactory

pytestmark = pytest.mark.django_db


def test_journal_lang_must_be_a_site_language():
    journal = JournalFactory.build(lang="de")

    with pytest.raises(ValidationError) as error:
        journal.full_clean()

    assert "lang" in error.value.message_dict


@pytest.mark.parametrize("lang", ["en", "lt"])
def test_journal_lang_accepts_a_site_language(lang):
    JournalFactory.build(lang=lang).full_clean()
