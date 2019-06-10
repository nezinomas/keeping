

def _round(number):
    return round(number, 2)


def _remove_line_end(rendered):
    return str(rendered).replace('\n', '')


def _print(*args):
    for a in args:
        print('\n\n>>>\n')
        print(a)
        print('\n<<<\n')
