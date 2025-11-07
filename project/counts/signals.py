from pathlib import Path

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.db.models import Model
from .models import CountType
from .services.model_services import CountTypeModelService


@receiver(post_save, sender=CountType)
@receiver(post_delete, sender=CountType)
def generate_counts_menu(sender: object, instance: Model, *args, **kwargs):
    user = instance.user
    qs = CountTypeModelService(user).objects

    if not qs:
        return

    journal = user.journal
    journal_pk = str(journal.pk)
    folder = Path(settings.MEDIA_ROOT) / journal_pk
    file = folder / "menu.html"

    if not folder.is_dir():
        folder.mkdir()

    content = render_to_string(
        template_name="counts/menu.html", context={"slugs": qs}, request=None
    )

    with open(file, "w+", encoding="utf-8") as f:
        f.write(content)
