from django.db import migrations

# MySQL's default collation makes "šviest" equal "sviest"; a Keyword's diacritics
# must agree, as normalise_keyword and the Match compare them. SQLite is binary.
ALTER = "ALTER TABLE `expenses_expensekeyword` MODIFY `keyword` varchar(100) NOT NULL"


def keyword_accent_sensitive(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    schema_editor.execute(f"{ALTER} COLLATE utf8mb4_bin")


def keyword_table_default(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    schema_editor.execute(ALTER)


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0005_expensekeyword"),
    ]

    operations = [
        migrations.RunPython(
            keyword_accent_sensitive, keyword_table_default, atomic=False
        ),
    ]
