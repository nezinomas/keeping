from django.conf import settings
from django.urls import include, path

urls = []

if settings.DEBUG:
    import mimetypes

    import debug_toolbar
    from django.conf.urls.static import static

    mimetypes.add_type("application/javascript", ".js", True)

    urls += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urls += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urls += [path('silk/', include('silk.urls', namespace='silk'))]
    urls = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urls
