from django.test import TestCase

from ..decorators.eval_string import sanitize_string


class TestSanitizeSting(TestCase):
    def test_sign_at_end(self):
        actual = '2+-'
        expected = '2'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_sign_at_start(self):
        actual = '+/-2'
        expected = '2'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_sign_at_start_and_end(self):
        actual = '+/-2*-'
        expected = '2'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_sign_in_middle(self):
        actual = '2+/-2'
        expected = '2+2'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_long_digit(self):
        actual = '0.123456'
        expected = '0.12'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_long_digit_no_trailing(self):
        actual = '.123456'
        expected = '0.12'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_two_long_digit(self):
        actual = '0.123456+10.12345'
        expected = '0.12+10.12'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_sign_full(self):
        actual = '-+2+/-2/*'
        expected = '2+2'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_addzeros_one_digit(self):
        actual = '.1'
        expected = '0.1'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_addzeros_two_digits(self):
        actual = '.1+.1'
        expected = '0.1+0.1'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)

    def test_sanitize_full(self):
        actual = '+/-*.123456+-0.1234*-0,1--'
        expected = '0.12+0.12*0.1'

        @sanitize_string
        def a(input):
            return input

        self.assertEqual(a(actual), expected)
