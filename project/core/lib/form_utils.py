from django.forms import BooleanField, ModelMultipleChoiceField


def add_css_class(instance):
    pass
    # default_input_css_class = []

    # for field_name in instance.fields:
    #     print(f'--------------------------->\nname {field_name} type {type(field_name)} - {type(instance.fields[field_name])}\n')
    #     if isinstance(instance.fields[field_name], (BooleanField, ModelMultipleChoiceField)):
    #         instance.fields[field_name].widget.attrs["class"] = " ".join(
    #         ['']
    #     )
    #     else :

    #     # if css_class := instance.fields[field_name].widget.attrs.get("class"):
    #     #     default_input_css_class.append(css_class)

    #         instance.fields[field_name].widget.attrs["class"] = " ".join(
    #             ['form-control-my']
    #         )


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
