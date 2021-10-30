from datetime import datetime


def chart_data(*args):
    cnt = 0
    if args:
        cnt = len(args[0])

    items = {'categories': cnt * [0], 'invested': cnt * [0], 'profit': cnt * [0]}

    for arr in args:
        for i in range(0, cnt):
            items['categories'][i] = arr[i]['year']
            items['invested'][i] += arr[i]['invested']
            items['profit'][i] += arr[i]['profit']

    rm = []
    for i in range(0, cnt):
        _y = items['categories'][i]
        _i = items['invested'][i]
        _p = items['profit'][i]

        if not _i and not _p:
            rm.append(i)

        if _y > datetime.now().year:
            rm.append(i)

    rm = list(set(rm)) # remove dublicate values
    rm.sort(reverse=True) # sort desc

    for i in rm:
        items['categories'].pop(i)
        items['invested'].pop(i)
        items['profit'].pop(i)

    return items
