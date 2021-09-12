from django import template

register = template.Library()


@register.filter
def bg_color(value):
    arr = {
        1: 'food',
        2: 'drinks',
        3: 'leisure',
        8: 'fees',
        9: 'work',
        11: 'fees',
        12: 'fees',
    }

    return arr.get(value, '')
