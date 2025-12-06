from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('administrators/', admin.site.urls),
    path('', include('main.urls')),
    path('inventory/', include('inventory.urls')),
    path('inventory-med/', include('inventory_meds.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
