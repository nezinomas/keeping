from importlib import import_module
from unittest.mock import MagicMock

import pytest

migration = import_module(
    "project.expenses.migrations.0006_expensekeyword_keyword_accent_sensitive"
)


def _schema_editor(vendor):
    schema_editor = MagicMock()
    schema_editor.connection.vendor = vendor
    return schema_editor


def test_keyword_collation_binary_on_mysql():
    schema_editor = _schema_editor("mysql")

    migration.keyword_accent_sensitive(None, schema_editor)

    sql = schema_editor.execute.call_args.args[0]
    assert "`expenses_expensekeyword`" in sql
    assert "COLLATE utf8mb4_bin" in sql


def test_keyword_collation_back_to_table_default_on_mysql():
    schema_editor = _schema_editor("mysql")

    migration.keyword_table_default(None, schema_editor)

    sql = schema_editor.execute.call_args.args[0]
    assert "`expenses_expensekeyword`" in sql
    assert "COLLATE" not in sql


@pytest.mark.parametrize(
    "operation",
    [migration.keyword_accent_sensitive, migration.keyword_table_default],
)
def test_keyword_collation_untouched_elsewhere(operation):
    schema_editor = _schema_editor("sqlite")

    operation(None, schema_editor)

    schema_editor.execute.assert_not_called()


def test_keyword_collation_runs_outside_a_transaction():
    # MySQL cannot roll DDL back, so Django refuses an ALTER inside atomic()
    (operation,) = migration.Migration.operations

    assert operation.atomic is False
