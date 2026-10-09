from django.core.exceptions import ValidationError


def set_journal_lang(user, lang):
    user.journal.lang = lang
    user.journal.save()


def validation_errors(instance):
    try:
        instance.full_clean()
    except ValidationError as error:
        return error.message_dict
    return {}
