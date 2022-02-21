from django import template

register = template.Library()


@register.filter
def bg_color(value):
    arr = {
        1: 'food',
        2: 'drinks',
        3: 'leisure',
        8: 'fee',
        9: 'work',
        11: 'fee',
        12: 'fee',
    }

    return arr.get(value, '')
