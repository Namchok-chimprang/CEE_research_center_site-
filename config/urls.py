from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('config.api_urls')),
    path('', include('apps.core.urls')),
    path('researchers/', include('apps.researchers.urls')),
    path('projects/', include('apps.projects.urls')),
    path('publications/', include('apps.publications.urls')),
    path('news/', include('apps.news.urls')),
    path('contact/', include('apps.contacts.urls')),
]

# Temporary production-safe fallback so media files are reachable on Render
# when using local filesystem storage.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
