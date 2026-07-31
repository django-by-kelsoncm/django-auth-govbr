from django.urls import path

from .views import GovBrCallbackView, GovBrLoginView, GovBrLogoutView

app_name = "django_govbr_auth"

urlpatterns = [
    path("login/", GovBrLoginView.as_view(), name="login"),
    path("callback/", GovBrCallbackView.as_view(), name="callback"),
    path("logout/", GovBrLogoutView.as_view(), name="logout"),
]
