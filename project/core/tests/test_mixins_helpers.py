import pytest
from ..mixins.helpers import format_plural


def test_url_name_model_name_single_word():
    actual = format_plural('saving')

    assert 'savings' == actual


def test_url_name_model_name_two_words():
    actual = format_plural('saving close')

    assert 'savings_close' == actual
