from ..lib.form_utils import clean_year_picker_input


def test_clean_year_input_no_field():
    field_name = "year"
    data = {}
    cleaned_data = {"A": 1}
    errors = {}
    actual = clean_year_picker_input(field_name, data, cleaned_data, errors)

    assert actual == cleaned_data


def test_clean_year_input_wrong_date_formating():
    field_name = "year"
    data = {"year": "1111.11.11"}
    cleaned_data = {"A": 1}
    errors = {}
    actual = clean_year_picker_input(field_name, data, cleaned_data, errors)

    assert actual == cleaned_data


def test_clean_year_input_wrong_date_type():
    field_name = "year"
    data = {"year": "xxxx-xx-xx"}
    cleaned_data = {"A": 1}
    errors = {}
    actual = clean_year_picker_input(field_name, data, cleaned_data, errors)

    assert actual == cleaned_data


def test_clean_year_input_year_out_of_unix_time():
    field_name = "year"
    data = {"year": "1973-12-31"}
    cleaned_data = {"A": 1}
    errors = {}
    actual = clean_year_picker_input(field_name, data, cleaned_data, errors)

    assert actual == cleaned_data


def test_clean_year_input_year_remove_error():
    field_name = "year"
    data = {"year": "1999-12-31"}
    cleaned_data = {"A": 1}
    errors = {"year": "Įveskite pilną skaičių", "foo": "boo"}
    actual = clean_year_picker_input(field_name, data, cleaned_data, errors)

    assert actual == {"A": 1, "year": "1999"}
    assert errors == {"foo": "boo"}
