from django.forms import BooleanField


def add_css_class(instance):
    for field_name in instance.fields:
        if isinstance(instance.fields[field_name], BooleanField):
            continue

        instance.fields[field_name].widget.attrs['class'] = 'form-control-sm'


def clean_year_picker_input(field_name, data, cleaned_data, errors):
    # ugly workaround for YearPickerInput field
    # widget returns YYYY-01-01 instead YYYY
    # is it possible to change backend_date_format?
    field = data.get(field_name)
    if not field:
        return cleaned_data
    # try split field by '-'
    try:
        field, *_ = field.split("-")
    except AttributeError:
        return cleaned_data
    # try convert field to int
    try:
        int(field)
    except ValueError:
        return cleaned_data
    # if field is in past
    if int(field) < 1974:
        return cleaned_data
    # if error for field exists in errors
    if errors.get(field_name):
        cleaned_data[field_name] = field
        errors.pop(field_name)

    return cleaned_data
