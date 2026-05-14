from pathlib import Path

from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from .models import CountType
from .services.model_services import CountTypeModelService


