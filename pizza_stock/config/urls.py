from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "",
        RedirectView.as_view(url="/reports/dashboard/", permanent=False),
        name="home",
    ),
    path("users/", include("users.urls")),
    path("branches/", include("branches.urls")),
    path("inventory/", include("inventory.urls")),
    path("sales/", include("sales.urls")),
    path("orders/", include("orders.urls")),
    path("order/", include("orders.public_urls")),
    path("forecast/", include("forecast.urls")),
    path("reports/", include("reports.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin
admin.site.site_header = "🍕 Pizza Stock Management"
admin.site.site_title = "Pizza Admin"
admin.site.index_title = "Welcome to Pizza Stock Management System"
