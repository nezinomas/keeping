def set_field_properties(self, helper):
    for field_name in self.fields:
        self.fields[field_name].widget.attrs['class'] = 'form-control-sm'

    helper.form_show_labels = False


class ChainedDropDown(object):
    def __init__(self, obj, parent_field_name):
        self._obj = obj
        self._id = None
        self._get_main_dropdown_id(parent_field_name)

    @property
    def parent_field_id(self) -> int:
        id = None

        try:
            id = int(self._id)
        except Exception:
            pass

        return id

    def _get_main_dropdown_id(self, parent_field_name):
        if parent_field_name in self._obj.data:
            self._id = self._obj.data.get(parent_field_name)

        elif self._obj.instance.pk:
            self._id = vars(self._obj.instance)[f'{parent_field_name}_id']
