
def add_session(client, *args, **kwargs):
    session = client.session

    for key, val in kwargs.items():
        session[key] = val

    session.save()
