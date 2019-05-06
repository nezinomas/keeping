from django.test import TestCase

from ..secrets import *


class SecretsTests(TestCase):
    def test_secrets_value_exists(self):
        actual = get_secret('FILENAME')
        expect = '_config_settings.json'
        self.assertEqual(expect, actual)

    def test_secrets_no_value_exeption_raise(self):
        self.assertRaises(ImproperlyConfigured, get_secret, 'XX')

    def test_secrets_file_not_found_raise_error(self):
        secrets = ReadConfigFile('FILE_DONT_EXISTS')
        with self.assertRaises(ImproperlyConfigured):
            get_secret('FILENAME', secrets.get_values)
