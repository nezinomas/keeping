import json
from datetime import date

import pytest

from ...expenses.tests.factories import ExpenseTypeFactory
from ...journals.models import Journal
from ..forms import SettingsForm, UnnecessaryForm
from .helpers import set_journal_lang

TODAY = date(1999, 2, 2)

pytestmark = pytest.mark.django_db


def test_form_fields(main_user):
    ExpenseTypeFactory(title="X")
    ExpenseTypeFactory(title="Y")
    form = UnnecessaryForm(user=main_user, today=TODAY).as_p()

    assert form.count('<input type="checkbox"') == 3


def test_form_selected_expenses(main_user):
    e1 = ExpenseTypeFactory(title="X")
    e2 = ExpenseTypeFactory(title="Y")

    main_user.journal.unnecessary_expenses = json.dumps([e1.pk, e2.pk])
    main_user.journal.save()

    form = UnnecessaryForm(user=main_user, today=TODAY).as_p()

    assert form.count("checked") == 2


def test_form_bad_json_for_expenses(main_user):
    ExpenseTypeFactory(title="X")
    ExpenseTypeFactory(title="Y")

    main_user.journal.unnecessary_expenses = "None"
    main_user.journal.save()

    form = UnnecessaryForm(user=main_user, today=TODAY).as_p()

    assert form.count("checked") == 0


def test_form_selected_savings(main_user):
    main_user.journal.unnecessary_savings = True
    main_user.journal.save()

    form = UnnecessaryForm(user=main_user, today=TODAY).as_p()

    assert form.count("checked") == 1


def test_form_save_checked_all(main_user):
    e1 = ExpenseTypeFactory(title="X")
    e2 = ExpenseTypeFactory(title="Y")
    form = UnnecessaryForm(
        user=main_user,
        today=TODAY,
        data={"savings": True, "choices": {e1.pk: True, e2.pk: True}},
    )

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == json.dumps([e1.pk, e2.pk])
    assert actual.unnecessary_savings


def test_form_refuses_more_expenses_than_the_column_holds(main_user):
    ticked = [ExpenseTypeFactory(title=f"T{i}").pk for i in range(100)]
    max_length = Journal._meta.get_field("unnecessary_expenses").max_length
    assert len(json.dumps(ticked)) > max_length

    form = UnnecessaryForm(
        user=main_user, today=TODAY, data={"savings": True, "choices": ticked}
    )

    assert not form.is_valid()
    assert form.errors["choices"] == ["Pažymėta per daug išlaidų rūšių."]


@pytest.mark.parametrize(
    "room, valid", [(0, True), (-1, False)], ids=["at_the_limit", "one_over"]
)
def test_form_takes_choices_up_to_the_column_length(
    main_user, monkeypatch, room, valid
):
    ticked = [ExpenseTypeFactory(title=f"T{i}").pk for i in range(3)]
    column = Journal._meta.get_field("unnecessary_expenses")
    monkeypatch.setattr(column, "max_length", len(json.dumps(ticked)) + room)

    form = UnnecessaryForm(
        user=main_user, today=TODAY, data={"savings": True, "choices": ticked}
    )

    assert form.is_valid() is valid


def test_form_save_checked_none(main_user):
    ExpenseTypeFactory(title="X")
    ExpenseTypeFactory(title="Y")
    form = UnnecessaryForm(
        user=main_user, today=TODAY, data={"savings": False, "choices": {}}
    )

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == "[]"
    assert not actual.unnecessary_savings


def test_form_save_unchecked_expenses(main_user):
    e1 = ExpenseTypeFactory(title="X")

    main_user.journal.unnecessary_expenses = json.dumps([e1.pk])
    main_user.journal.save()

    form = UnnecessaryForm(
        user=main_user, today=TODAY, data={"savings": False, "choices": {}}
    )

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == "[]"
    assert not actual.unnecessary_savings


@pytest.mark.parametrize(
    "expected",
    [
        ('<select name="lang"', '<input type="text" name="title"'),
        ("Svetainės kalba:", "Svetainės pavadinimas:"),
    ],
    ids=["fields", "translation"],
)
def test_settings_form_fields(expected, main_user):
    form = SettingsForm(user=main_user, today=TODAY).as_p()

    for substring in expected:
        assert substring in form


def test_settings_form_languages(main_user):
    form = SettingsForm(user=main_user, today=TODAY).as_p()

    assert form.count("<option value=") == 2


def test_settings_form_lang_initial(main_user):
    set_journal_lang(main_user, "en")

    form = SettingsForm(user=main_user, today=TODAY).as_p()

    assert '<option value="en" selected>Anglų</option>' in form


def test_settings_form_title_initial(main_user):
    form = SettingsForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="title" value="bob Journal"' in form


def test_settings_form_save(main_user):
    form = SettingsForm(
        user=main_user, today=TODAY, data={"title": "zzz", "lang": "lt"}
    )

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()

    assert actual.lang == "lt"
    assert actual.title == "zzz"


def test_settings_form_save_lang_invalid(main_user):
    form = SettingsForm(user=main_user, today=TODAY, data={"title": "zzz", "lang": "x"})

    assert not form.is_valid()


@pytest.mark.parametrize(
    "title",
    ["xx", "x" * 255, "x" * 101, "My@Journal"],
    ids=["too_short", "255_chars", "101_chars", "bad_char"],
)
def test_settings_form_title_follows_journal_title(title, main_user):
    form = SettingsForm(
        user=main_user, today=TODAY, data={"title": title, "lang": "en"}
    )

    assert not form.is_valid()

    assert "title" in form.errors


@pytest.mark.parametrize(
    "title, lang, message",
    [
        (
            "...",
            "lt",
            "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo.",
        ),
        ("Pienas ½ l", "lt", "Pavadinime negali būti „½“."),
        (
            "x" * 101,
            "en",
            "Įsitikinkite, kad reikšmė sudaryta iš nedaugiau kaip 100 ženklų "
            "(dabartinis ilgis 101).",
        ),
    ],
    ids=["empty_slug", "expanding_character", "too_long_says_so_once"],
)
def test_settings_title_error_message(title, lang, message, main_user):
    form = SettingsForm(
        user=main_user, today=TODAY, data={"title": title, "lang": lang}
    )

    assert not form.is_valid()

    assert form.errors["title"] == [message]
