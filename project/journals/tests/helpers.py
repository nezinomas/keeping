def set_journal_lang(user, lang):
    user.journal.lang = lang
    user.journal.save()
