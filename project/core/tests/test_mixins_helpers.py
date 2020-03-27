from ..mixins.helpers import format_plural


def test_url_name_model_name_single_word():
    actual = format_plural('saving')

    assert actual == 'savings'


def test_url_name_model_name_two_words():
    actual = format_plural('saving close')

    assert actual == 'savings_close'
