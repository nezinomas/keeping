def set_field_properties(self, helper):
    for field_name in self.fields:
        self.fields[field_name].widget.attrs['class'] = 'form-control-sm'

    helper.form_show_labels = False
