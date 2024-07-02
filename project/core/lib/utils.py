from crequest.middleware import CrequestMiddleware


def get_user():
    request = CrequestMiddleware.get_request()
    return request.user


def get_request_kwargs(name):
    crequest = CrequestMiddleware.get_request()
    return crequest.resolver_match.kwargs.get(name) if crequest else None


def total_row(data, fields) -> dict:
    row = {field: sum(getattr(d, field, 0) for d in data) for field in fields}

    if not row.get("profit_proc"):
        return row

    row["profit_proc"] = calculate_percents(row)

    return row

def calculate_percents(data):
    incomes = data.get("incomes", 0)
    fee = data.get("fee", 0)
    market_value = data.get("market_value", 0)

    return ((market_value - fee) / incomes * 100) - 100 if incomes else 0