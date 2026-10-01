from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

validate_title_characters = RegexValidator(
    regex=r"^[ \w\-\.]+$",
    message=_(
        "Title can only contain letters, numbers, spaces, hyphens, and underscores."
    ),
)


def expanding_characters_in(value: str) -> list[str]:
    return [
        character for character in dict.fromkeys(value) if len(slugify(character)) > 1
    ]


def validate_title_slug(value: str) -> None:
    if not slugify(value):
        raise ValidationError(
            _("Title must contain at least one Latin letter or digit."),
            code="empty_slug",
        )

    # slugify writes these as several letters, so the slug would outgrow its column
    if characters := expanding_characters_in(value):
        raise ValidationError(
            _("Title cannot contain “%(characters)s”."),
            code="expanding_characters",
            params={"characters": ", ".join(characters)},
        )


TITLE_VALIDATORS = [MinLengthValidator(3), validate_title_slug]
