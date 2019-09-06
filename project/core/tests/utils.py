def equal_list_of_dictionaries(expect, actual):
    for key, arr in enumerate(expect):
        for expect_key, expect_val in arr.items():
            if expect_key not in actual[key]:
                raise Exception(
                    f'No \'{expect_key}\' key in {actual[key]}. List item: {key}')

            actual_val = actual[key][expect_key]

            try:
                actual_val = float(actual_val)
            except:
                pass

            if expect_val != actual_val:
                raise Exception(
                    f'Not Equal.'
                    f'Expected: {expect_key}={expect_val} '
                    f'Actual: {expect_key}={actual[key][expect_key]}\n\n'
                    f'Expected:\n{expect}\n\n'
                    f'Actual:\n{actual}\n'
                )

def _round(number):
    return round(number, 2)


def _remove_line_end(rendered):
    return str(rendered).replace('\n', '')


def _print(*args):
    for a in args:
        print('\n\n>>>\n')
        print(a)
        print('\n<<<\n')
