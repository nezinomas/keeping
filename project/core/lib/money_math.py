from decimal import Decimal, ROUND_HALF_UP

from ..decorators.eval_string import sanitize_string


@sanitize_string
def string_to_sum(input):
    sum = eval(input)
    sum = 0 if sum < 0 else sum

    return sum


@sanitize_string
def total(*args):
    price = 0
    for arg in args:
        price += Decimal(arg)

    return price.quantize(Decimal('.01'), ROUND_HALF_UP)
