def calc_percent(args):
    market = args[0]
    invested = args[1]

    rtn = 0.0
    if market and invested:
        rtn = ((market * 100) / invested) - 100

    return rtn


def calc_sum(args):
    market = args[0]
    invested = args[1]

    return market - invested


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
