from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

validate_title_characters = RegexValidator(
    regex=r"^[ \w\-\.]+$",
    message=_(
        "Title can only contain letters, numbers, spaces, hyphens, and underscores."
    ),
)


def validate_title_slug(value: str) -> None:
    if not slugify(value):
        raise ValidationError(
            _("Title must contain at least one Latin letter or digit."),
            code="empty_slug",
        )
