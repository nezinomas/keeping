from types import SimpleNamespace

from ..helpers.helper_forms import ChainedDropDown


# ----------------------------------------------------------------------------
#                                                              ChainedDropDown
# ----------------------------------------------------------------------------
def test_update_event_then_data_dict_not_empty():
    obj = SimpleNamespace(data={'ex_type': 99})
    actual = ChainedDropDown(obj, 'ex_type').parent_field_id

    assert actual == 99


def test_update_event_then_data_dict_empty_but_exists_instance():
    obj = SimpleNamespace(
        data={},
        instance=SimpleNamespace(
            pk=1,
            ex_type='Name',
            ex_type_id=11
        )
    )
    actual = ChainedDropDown(obj, 'ex_type').parent_field_id

    assert actual == 11


def test_id_int_as_string():
    obj = SimpleNamespace(data={'e': '99'})
    actual = ChainedDropDown(obj, 'e').parent_field_id

    assert actual == 99


def test_id_string():
    obj = SimpleNamespace(data={'e': 'x'})
    actual = ChainedDropDown(obj, 'e').parent_field_id

    assert not actual


def test_id_float():
    obj = SimpleNamespace(data={'e': 4.5})
    actual = ChainedDropDown(obj, 'e').parent_field_id

    assert actual == 4
