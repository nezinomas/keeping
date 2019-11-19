from ..factories import UserFactory


def test_user_str():
    actual = UserFactory.build()

    assert str(actual) == 'bob'
