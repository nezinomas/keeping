import re


def __add_zeros(input):
    if type(input) == str:
        #
        digits = re.split(r'[^\d\.]', input)
        signs = re.split(r'[\d\.]+', input)

        for idx, val in enumerate(digits):
            regex = re.compile('^\.\d+')
            if re.match(regex, val) is not None:
                digits[idx] = '0{}'.format(val)

        return ''.join([a + b for a, b in zip(signs, digits)])


def __remove_excess_symbols(input):
    input = input.replace(',', '.')
    # remove non digits ant non math signs
    input = re.sub('[^0-9\*\+\-\/\.]', '', input)
    return input


def __remove_excess_math_signs(input):
    # remove double math signs
    pattern = re.compile(r'([\+\/\-\*]{2,})')
    for group in re.finditer(pattern, input):
        _group = group.group(1)
        input = input.replace(_group, _group[0])

    # remove math signs at end
    input = re.sub(r'([^\d]+)$', r'', input)

    # remove math signs at start
    input = re.sub(r'^([^\d\.]+)', r'', input)

    return input


def __remove_digits(input):
    # 0.23578 -> 0.23
    return re.sub(r'(\.\d{2})(\d+)', r'\1', input)


def sanitize_string(func):
    def func_wrapper(*args):
        returnList = []
        for input in args:
            if type(input) == str:
                input = __remove_excess_symbols(input)
                input = __remove_excess_math_signs(input)
                input = __add_zeros(input)
                input = __remove_digits(input)

            returnList.append(input)
        return func(*returnList)
    return func_wrapper
