"""
URL Configuration - Web Security Demo
- /api/* -> JWT auth (Vite SPA)
- /api/docs/ -> Swagger UI
- /api/redoc/ -> Redoc
- /shop/* -> Cookie/Session auth (Django templates)
- /admin/ -> Django admin
- When SPA_ROOT is set: /assets/, /images/ and /* serve the Vite SPA
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import FileResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def spa_index(request):
    """Serve SPA index.html for client-side routing."""
    index_path = settings.SPA_ROOT / 'index.html'
    if not index_path.exists():
        from django.http import HttpResponse
        return HttpResponse('SPA not built. Set SPA_ROOT and build frontend.', status=404)
    return FileResponse(open(index_path, 'rb'), content_type='text/html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('shop.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('shop/', include('shop.urls')),
]

# Production: serve Vite SPA from SPA_ROOT
if getattr(settings, 'SPA_ROOT', None):
    urlpatterns += [
        path('assets/<path:path>', serve, {'document_root': settings.SPA_ROOT / 'assets'}),
        path('images/<path:path>', serve, {'document_root': settings.SPA_ROOT / 'images'}),
        re_path(r'^(?!api/|admin/|shop/|static/|media/).*', spa_index),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
