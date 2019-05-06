from decimal import Decimal, ROUND_HALF_UP

from django.test import TestCase

from ..lib import money_math as T


class TestStringToSum(TestCase):
    def test_str2sum_negative_sum(self):
        actual = '.1-10'
        expected = 0
        self.assertEqual(T.string_to_sum(actual), expected)

    def test_str2sum_common_input(self):
        actual = '.99*2+.1*2'
        expected = 2.18
        self.assertEqual(T.string_to_sum(actual), expected)


class TestTotal(TestCase):
    def test_total_sum_mixed_input(self):
        actual = [1, ',9999', '1.9999', 2.9999]
        expect = Decimal(6.98)
        self.assertAlmostEqual(T.total(*actual), expect)
