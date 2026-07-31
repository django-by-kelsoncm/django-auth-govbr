from django.urls import include, path

urlpatterns = [
    path("auth/govbr/", include("django_govbr_auth.urls")),
]
