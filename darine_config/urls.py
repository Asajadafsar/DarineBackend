from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('gold/', include('gold_app.urls')),
    # path('silver/', include('silver_app.urls')), # اگر برای نقره هم یو‌آر‌ال مجزا داری
] 

# این بخش برای نمایش تصاویر رسید در محیط توسعه (Local) حیاتی است
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)