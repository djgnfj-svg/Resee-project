"""
API Documentation configuration for Resee project.
Swagger/OpenAPI schema customization and additional documentation.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# Global security definitions
SECURITY_DEFINITIONS = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header',
        'description': 'JWT 토큰을 사용한 인증. 형식: `Bearer <token>`'
    }
}

# Global responses
GLOBAL_RESPONSES = {
    400: openapi.Response(
        description="잘못된 요청",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING, description="에러 메시지"),
                'details': openapi.Schema(type=openapi.TYPE_OBJECT, description="상세 에러 정보")
            }
        )
    ),
    401: openapi.Response(
        description="인증 필요",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description="인증 에러 메시지")
            }
        )
    ),
    403: openapi.Response(
        description="권한 없음",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description="권한 에러 메시지")
            }
        )
    ),
    404: openapi.Response(
        description="리소스를 찾을 수 없음",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Not found")
            }
        )
    ),
    429: openapi.Response(
        description="요청 한도 초과",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Rate limit exceeded")
            }
        )
    ),
    500: openapi.Response(
        description="서버 내부 오류",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Internal server error")
            }
        )
    )
}

# API Tags
API_TAGS = [
    {
        'name': 'Authentication',
        'description': '🔐 사용자 인증 및 토큰 관리'
    },
    {
        'name': 'Accounts',
        'description': '👤 사용자 계정 및 프로필 관리'
    },
    {
        'name': 'Content',
        'description': '📚 학습 콘텐츠 및 카테고리 관리'
    },
    {
        'name': 'Review',
        'description': '🔄 복습 스케줄 및 이력 관리'
    },
    {
        'name': 'AI Review',
        'description': '🤖 AI 기반 문제 생성 및 분석'
    },
    {
        'name': 'Analytics',
        'description': '📊 학습 분석 및 통계'
    },
    {
        'name': 'Monitoring',
        'description': '⚙️ 시스템 모니터링 및 헬스체크'
    }
]


def get_custom_schema_view():
    """
    Get customized schema view with enhanced documentation
    """
    return get_schema_view(
        openapi.Info(
            title="Resee API",
            default_version='v1.0',
            description="""
            # 🧠 Resee - 과학적 복습 플랫폼 API
            
            **에빙하우스 망각곡선에 기반한 스마트 복습 시스템의 공식 API 문서**
            
            ## 🎯 주요 기능
            - **🔐 인증 시스템**: JWT 토큰 기반 인증 및 Google OAuth
            - **📚 콘텐츠 관리**: 학습 콘텐츠 CRUD 및 카테고리 관리
            - **🔄 복습 시스템**: 과학적 복습 스케줄링 및 이력 관리
            - **🤖 AI 기능**: 자동 문제 생성 및 개인화된 학습 분석
            - **📊 분석 기능**: 학습 패턴 분석 및 성과 대시보드
            - **⚙️ 모니터링**: 시스템 헬스체크 및 성능 모니터링
            
            ## 🚀 빠른 시작
            
            ### 1. 인증하기
            ```bash
            curl -X POST http://localhost:8000/api/auth/token/ \\
              -H "Content-Type: application/json" \\
              -d '{"email": "test@resee.com", "password": "test123!"}'
            ```
            
            ### 2. API 호출하기
            ```bash
            curl -X GET http://localhost:8000/api/content/contents/ \\
              -H "Authorization: Bearer <your_access_token>"
            ```
            
            ## 📖 복습 시스템 원리
            
            **에빙하우스 망각곡선 기반 간격 반복**:
            - 1일 → 3일 → 7일 → 14일 → 30일 → 60일
            - 틀린 문제는 처음부터 다시 시작
            - 맞춘 문제는 다음 간격으로 이동
            
            ## 🔑 테스트 계정
            - **admin@resee.com** / admin123! (관리자)
            - **test@resee.com** / test123! (일반 사용자)
            - **demo@resee.com** / demo123! (데모 사용자)
            
            ## 📈 Rate Limiting
            - **로그인**: 5회/분
            - **회원가입**: 3회/시간  
            - **AI 기능**: 구독별 차등 (10-200회/시간)
            - **일반 API**: 1000회/시간
            
            ## 🔒 보안
            - 모든 API는 HTTPS를 통해 제공됩니다
            - JWT 토큰은 60분 후 만료됩니다
            - Refresh 토큰은 7일 후 만료됩니다
            - Rate limiting으로 남용을 방지합니다
            """,
            terms_of_service="https://resee.com/terms/",
            contact=openapi.Contact(
                name="Resee API Support",
                email="api@resee.com",
                url="https://resee.com/support/"
            ),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )


# Common parameter definitions
COMMON_PARAMETERS = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="페이지 번호 (기본값: 1)",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="페이지당 항목 수 (기본값: 20, 최대: 100)",
        type=openapi.TYPE_INTEGER,
        default=20
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="검색 키워드",
        type=openapi.TYPE_STRING
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="정렬 기준 (예: created_at, -created_at)",
        type=openapi.TYPE_STRING
    )
}