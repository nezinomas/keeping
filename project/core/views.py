from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .lib.date import years
from .lib.utils import get_safe_redirect
from .mixins.views import TemplateViewMixin


@login_required()
def set_year(request, year):
    user = request.user
    if year in years(user):
        user.year = year
        user.save()

    return redirect(get_safe_redirect(request, request.META.get("HTTP_REFERER")))


class ModalImage(TemplateViewMixin):
    template_name = "core/modal_image.html"
