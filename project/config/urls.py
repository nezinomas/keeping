from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('project.auths.urls')),
    path('', include('project.accounts.urls')),
    path('', include('project.bookkeeping.urls')),
    path('', include('project.books.urls')),
    path('', include('project.core.urls')),
    path('', include('project.drinks.urls')),
    path('', include('project.expenses.urls')),
    path('', include('project.incomes.urls')),
    path('', include('project.savings.urls')),
    path('', include('project.plans.urls')),
    path('', include('project.transactions.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    from django.views.defaults import server_error, page_not_found, permission_denied

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns += [
        path(
            '403/',
            permission_denied,
            kwargs={'exception': Exception("Permission Denied")}, name='error403'
        ),
        path(
            '404/',
            page_not_found,
            kwargs={'exception': Exception("Page not Found")}, name='error404'
        ),
        path(
            '500/',
            server_error,
            name='error500'
        ),
    ]

    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
