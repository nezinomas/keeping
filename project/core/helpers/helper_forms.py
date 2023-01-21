from django.forms import BooleanField


def set_field_properties(self, helper):
    for field_name in self.fields:
        if isinstance(self.fields[field_name], BooleanField):
            continue
        self.fields[field_name].widget.attrs['class'] = 'form-control-sm'

    helper.form_show_labels = False
