def calc_percent(args):
    market = args[0]
    invested = args[1]

    if market and invested:
        return ((market * 100) / invested) - 100

    return 0.0


def calc_sum(args):
    market = args[0]
    invested = args[1]

    if market:
        return market - invested

    return 0.0
