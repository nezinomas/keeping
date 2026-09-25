import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ...services.review_choices import ReviewChoices
from ..factories import ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


def test_load_runs_exactly_two_queries(main_user):
    t = ExpenseTypeFactory()
    ExpenseNameFactory(title="N1", parent=t)
    ExpenseNameFactory(title="N2", parent=t)

    with CaptureQueriesContext(connection) as ctx:
        ReviewChoices.load(main_user, 1999)

    assert len(ctx.captured_queries) == 2


def test_load_excludes_the_other_journals_types_and_names(main_user, second_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="N1", parent=t)

    foreign_t = ExpenseTypeFactory(title="Foreign", journal=second_user.journal)
    ExpenseNameFactory(title="Foreign name", parent=foreign_t)

    choices = ReviewChoices.load(main_user, 1999)

    assert choices.types == (t,)
    assert choices.names == (n,)


def test_load_excludes_a_name_not_valid_for_the_year(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="N-1999", parent=t, valid_for=1999)
    ExpenseNameFactory(title="N-2005", parent=t, valid_for=2005)

    choices = ReviewChoices.load(main_user, 1999)

    assert choices.names == (n,)


def test_names_for_picks_one_types_names(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    n1 = ExpenseNameFactory(title="N1", parent=t1)
    ExpenseNameFactory(title="N2", parent=t2)

    choices = ReviewChoices.load(main_user, 1999)

    assert choices.names_for(t1.pk) == (n1,)


def test_names_for_zero_is_empty(main_user):
    t = ExpenseTypeFactory()
    ExpenseNameFactory(title="N1", parent=t)

    choices = ReviewChoices.load(main_user, 1999)

    assert choices.names_for(0) == ()
