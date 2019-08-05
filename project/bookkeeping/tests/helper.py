def assert_(expected, actual):
    for saving_type, arr in expected.items():
        for _k, expected_val in expected[saving_type].items():
            actual_val = actual[saving_type][_k]

            try:
                actual_val = round(float(actual_val), 2)
            except:
                pass

            msg = f'{saving_type}->{_k}. Expected={expected_val} Actual={actual_val}'

            assert expected_val == actual_val, msg
