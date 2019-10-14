from django.urls import resolve, reverse


def equal_list_of_dictionaries(expect, actual):
    for key, arr in enumerate(expect):
        for expect_key, expect_val in arr.items():
            if expect_key not in actual[key]:
                raise Exception(
                    f'No \'{expect_key}\' key in {actual[key]}. List item: {key}')

            actual_val = actual[key][expect_key]

            try:
                actual_val = float(actual_val)
                actual_val = round(actual_val, 2)
            except:
                pass

            if expect_val != actual_val:
                raise Exception(
                    f'Not Equal.'
                    f'Expected: {expect_key}={expect_val} '
                    f'Actual: {expect_key}={actual[key][expect_key]}\n\n'
                    f'Expected:\n{expect}\n\n'
                    f'Actual:\n{actual}\n'
                )


def _remove_line_end(rendered):
    return str(rendered).replace('\n', '').replace('\t', '')


def change_profile_year(client, year=1):
    url = reverse('core:core_index')
    response = client.get(url)

    u = response.wsgi_request.user
    u.profile.year = year
    u.save()


def setup_view(view, request, *args, **kwargs):
    """
    Mimic ``as_view()``, but returns view instance.
    Use this function to get view instances on which you can run unit tests,
    by testing specific methods.
    """

    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view
