from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.http import HttpResponse  # اضافه کنید


# ویو ساده برای صفحه اصلی
def home_view(request):
    # گزینه 1: برگرداندن یک پیام ساده
    return HttpResponse("""
        <h1>به پروژه Darine خوش آمدید!</h1>
        <ul>
            <li><a href="/panel/">پنل مدیریت</a></li>
            <li><a href="/gold/">بخش طلا</a></li>
            <li><a href="/silver/">بخش نقره</a></li>
            <li><a href="/api/docs/">مستندات API</a></li>
        </ul>
    """)


urlpatterns = [
    path("", home_view, name="home"),  # این خط را اضافه کنید
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("gold/", include("gold_app.urls")),
    path("silver/", include("silver_app.urls")),
    path("panel/", include("admin_panel.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# این بخش برای نمایش تصاویر رسید در محیط توسعه (Local) حیاتی است
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
