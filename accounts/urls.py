from django.urls import path, include
from django.conf import settings

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

app_name = 'accounts'

urlpatterns = [
    path('api/v1/', include('accounts.api.v1.urls'), name='api-v1'),
]

ADMIN_EMAIL = getattr(settings, 'EMAIL_HOST_USER', 'admin@web-site.com')

# SWAGGER - BEGIN
schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        # description="",
        # terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email=ADMIN_EMAIL),
        license=openapi.License(name="MIT License"),
    ),
    public=False,
    permission_classes=[permissions.IsAdminUser],
)

urlpatterns += [path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),]
# SWAGGER - END
