from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_title_characters = RegexValidator(
    regex=r"^[\w \-]+$",
    message=_(
        "Title can only contain letters, numbers, spaces, hyphens, and underscores."
    ),
)
