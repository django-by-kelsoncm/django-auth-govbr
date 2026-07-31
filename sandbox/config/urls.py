from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/govbr/", include("django_govbr_auth.urls")),
    path("", include("home.urls")),
]
