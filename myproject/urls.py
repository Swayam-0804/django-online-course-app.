"""URL configuration for the Online Course project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("onlinecourse/", include("onlinecourse.urls")),
    path("", RedirectView.as_view(pattern_name="onlinecourse:index", permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
