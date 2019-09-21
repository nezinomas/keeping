import pytest
from ..mixins.helpers import format_url_name


def test_url_name_model_name_single_word():
    actual = format_url_name('saving')

    assert 'savings' == actual


def test_url_name_model_name_two_words():
    actual = format_url_name('saving close')

    assert 'savings_close' == actual
