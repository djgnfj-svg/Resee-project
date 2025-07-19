"""
URL configuration for resee project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from accounts.views import EmailTokenObtainPairView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Resee API",
        default_version='v1',
        description="""
        # 📚 Resee - 과학적 복습 플랫폼 API
        
        **에빙하우스 망각곡선에 기반한 스마트 복습 시스템 API 문서**
        
        ## 🎯 주요 기능
        - **인증 시스템**: JWT 토큰 기반 인증
        - **콘텐츠 관리**: 학습 콘텐츠 CRUD
        - **복습 시스템**: 스마트 복습 스케줄링
        - **분석 기능**: 학습 통계 및 대시보드
        
        ## 🔐 인증 방법
        1. `/api/auth/token/` 엔드포인트로 로그인
        2. 받은 `access` 토큰을 헤더에 포함: `Authorization: Bearer <token>`
        
        ## 📖 복습 간격
        - 1일 → 3일 → 7일 → 14일 → 30일 (에빙하우스 망각곡선 기반)
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@resee.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication
    path('api/auth/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/content/', include('content.urls')),
    path('api/review/', include('review.urls')),
    path('api/analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)