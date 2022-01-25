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


def calc_balance(args) -> float:
    """[summary]

    Args:
        args[0] = past: [float]

        args[1] = incomes: [float]

        args[2] = expenses: [float]

    Returns:
        float:
    """

    past = args[0]
    incomes = args[1]
    expenses = args[2]

    return (
        0.0
        + past
        + incomes
        - expenses
    )


def calc_delta(args) -> float:
    """[summary]

    Args:
        args[0] = have: [float]

        args[1] = balance: [float]

    Returns:
        float
    """

    have = args[0]
    balance = args[1]

    return (
        0.0
        + have
        - balance
    )
