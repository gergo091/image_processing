from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

from apps.frontend.views import HomeView, TaskStatusView

urlpatterns = [
    # Examples:
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', HomeView.as_view(), name='home'),
    url(
        r'^task-status/(?P<task_id>[\-\w]+)$',
        TaskStatusView.as_view(),
        name='status'
    ),
    url(r'^api/', include('apps.api_urls')),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    # static files
    urlpatterns += staticfiles_urlpatterns()
    # media files
    urlpatterns += patterns(
        '',
        url(
            r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT},
        ),
        url(
            r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT},
        ),
    )
