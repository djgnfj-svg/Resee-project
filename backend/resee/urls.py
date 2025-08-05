"""
URL configuration for resee project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from accounts.views import EmailTokenObtainPairView
from .health import health_check, detailed_health_check, readiness_check, liveness_check

# API documentation schema
schema_view = get_schema_view(
    openapi.Info(
        title="Resee API",
        default_version='v1',
        description="Resee 스마트 복습 플랫폼 API",
        contact=openapi.Contact(email="admin@resee.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health checks
    path('api/health/', health_check, name='health'),
    path('api/health/detailed/', detailed_health_check, name='detailed_health'),
    path('api/health/ready/', readiness_check, name='readiness'),
    path('api/health/live/', liveness_check, name='liveness'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Convenient API docs shortcuts
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs-swagger'),
    path('api/docs/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='api-docs-redoc'),
    
    # Authentication
    path('api/auth/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/content/', include('content.urls')),
    path('api/review/', include('review.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/ai-review/', include('ai_review.urls')),
    path('api/monitoring/', include('monitoring.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)