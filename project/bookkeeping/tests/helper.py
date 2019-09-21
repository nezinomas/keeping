def assert_(expected, actual):
    for saving_type, arr in expected.items():
        for _k, expected_val in expected[saving_type].items():
            try:
                actual_val = actual[saving_type][_k]
            except:
                raise Exception(f'No \'{_k}\' key in {actual[saving_type]}.')

            try:
                actual_val = round(float(actual_val), 2)
            except:
                pass

            msg = f'{saving_type}->{_k}. Expected={expected_val} Actual={actual_val}'

            assert expected_val == actual_val, msg


def filter_fixture(data, leave_keys):
    rm_keys = set(data.keys()) - set(leave_keys)

    for key in rm_keys:
        data.pop(key)
