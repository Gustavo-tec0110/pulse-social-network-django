from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from network.api import RegisterAPIView, api_router
from network.views import health_check, home


urlpatterns = [
    path("", home, name="home"),
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("network.urls")),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/register/", RegisterAPIView.as_view(), name="api-register"),
    path("api/", include(api_router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
