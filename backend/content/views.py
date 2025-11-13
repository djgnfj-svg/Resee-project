import logging

from django.core.exceptions import ValidationError
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from resee.cache_utils import CacheManager, cached_method
from resee.mixins import AuthorViewSetMixin, UserOwnershipMixin
from resee.pagination import ContentPagination, OptimizedPageNumberPagination
# Performance monitoring removed for production
from resee.structured_logging import (log_api_call, log_performance,
                                      performance_logger)

from .models import Category, Content
from .serializers import CategorySerializer, ContentSerializer
from ai_services import validate_content
from accounts.subscription.services import PermissionService

logger = logging.getLogger(__name__)


class CategoryViewSet(UserOwnershipMixin, viewsets.ModelViewSet):
    """
    카테고리 관리
    
    학습 콘텐츠를 분류하기 위한 카테고리를 관리합니다.
    전역 카테고리와 사용자별 커스텀 카테고리를 지원합니다.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    @swagger_auto_schema(
        operation_summary="카테고리 목록 조회",
        operation_description="사용자의 개인 커스텀 카테고리 목록을 반환합니다.",
        responses={200: CategorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Add category usage metadata to response
        if hasattr(response, 'data'):
            response.data = {
                'results': response.data.get('results', response.data),
                'usage': PermissionService(request.user).get_category_usage(),
                'count': response.data.get('count') if isinstance(response.data, dict) else len(response.data),
                'next': response.data.get('next') if isinstance(response.data, dict) else None,
                'previous': response.data.get('previous') if isinstance(response.data, dict) else None,
            }
        return response
    
    @swagger_auto_schema(
        operation_summary="새 카테고리 생성",
        operation_description="새로운 개인 커스텀 카테고리를 생성합니다. 이모지나 색상은 name 필드에 포함 가능합니다.",
        request_body=CategorySerializer,
        responses={
            201: CategorySerializer(),
            402: openapi.Response(
                description="카테고리 생성 제한 초과",
                examples={
                    "application/json": {
                        "error": "카테고리 생성 제한에 도달했습니다",
                        "usage": {
                            "current": 3,
                            "limit": 3,
                            "tier": "free"
                        },
                        "message": "더 많은 카테고리를 생성하려면 구독을 업그레이드하세요"
                    }
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        # Check category creation limit
        user = request.user
        if not PermissionService(user).can_create_category():
            usage = PermissionService(user).get_category_usage()
            return Response({
                'error': '카테고리 생성 제한에 도달했습니다',
                'usage': usage,
                'message': '더 많은 카테고리를 생성하려면 구독을 업그레이드하세요'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        return super().create(request, *args, **kwargs)



class ContentViewSet(AuthorViewSetMixin, viewsets.ModelViewSet):
    """
    학습 콘텐츠 관리
    
    사용자의 학습 콘텐츠를 생성, 수정, 삭제, 조회할 수 있습니다.
    필터링, 정렬 기능을 지원합니다.
    """
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    pagination_class = ContentPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    # Query optimization configuration
    select_related_fields = ['category', 'author']
    prefetch_related_fields = ['review_history', 'review_schedules']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Category filter
        category_slug = self.request.query_params.get('category_slug', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset
    
    @swagger_auto_schema(
        operation_summary="콘텐츠 목록 조회",
        operation_description="사용자의 모든 학습 콘텐츠를 조회합니다. 필터링, 정렬이 가능합니다.",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="카테고리로 필터링", type=openapi.TYPE_INTEGER),
            openapi.Parameter('category_slug', openapi.IN_QUERY, description="카테고리 슬러그로 필터링", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="제목 및 내용에서 검색", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="정렬 (-created_at, title, updated_at)", type=openapi.TYPE_STRING),
        ],
        responses={200: ContentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Add content usage metadata to response
        if hasattr(response, 'data'):
            response.data = {
                'results': response.data.get('results', response.data),
                'usage': PermissionService(request.user).get_content_usage(),
                'count': response.data.get('count') if isinstance(response.data, dict) else len(response.data),
                'next': response.data.get('next') if isinstance(response.data, dict) else None,
                'previous': response.data.get('previous') if isinstance(response.data, dict) else None,
            }
        return response
    
    @swagger_auto_schema(
        operation_summary="새 콘텐츠 생성",
        operation_description="새로운 학습 콘텐츠를 생성합니다. 자동으로 복습 스케줄이 생성됩니다.",
        request_body=ContentSerializer,
        responses={
            201: ContentSerializer(),
            402: openapi.Response(
                description="콘텐츠 생성 제한 초과",
                examples={
                    "application/json": {
                        "error": "콘텐츠 생성 제한에 도달했습니다",
                        "usage": {
                            "current": 10,
                            "limit": 10,
                            "tier": "free"
                        },
                        "message": "더 많은 콘텐츠를 생성하려면 구독을 업그레이드하세요"
                    }
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        # Check content creation limit
        user = request.user
        if not PermissionService(user).can_create_content():
            usage = PermissionService(user).get_content_usage()
            return Response({
                'error': '콘텐츠 생성 제한에 도달했습니다',
                'usage': usage,
                'message': '더 많은 콘텐츠를 생성하려면 구독을 업그레이드하세요'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="콘텐츠 상세 조회",
        operation_description="특정 콘텐츠의 상세 정보를 조회합니다.",
        responses={200: ContentSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="콘텐츠 수정",
        operation_description="기존 콘텐츠를 수정합니다.",
        request_body=ContentSerializer,
        responses={200: ContentSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="콘텐츠 삭제",
        operation_description="콘텐츠를 삭제합니다. 관련된 복습 스케줄도 함께 삭제됩니다.",
        responses={204: "삭제 완료"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    
    @swagger_auto_schema(
        operation_summary="카테고리별 콘텐츠 조회",
        operation_description="콘텐츠를 카테고리별로 그룹화하여 반환합니다.",
        responses={200: openapi.Response(
            description="카테고리별로 그룹화된 콘텐츠",
            examples={
                "application/json": {
                    "english": {
                        "category": {"id": 1, "name": "영어", "slug": "english"},
                        "contents": [{"id": 1, "title": "영어 단어"}],
                        "count": 1
                    }
                }
            }
        )}
    )
    @action(detail=False, methods=['get'])
    @cached_method(timeout=600, key_prefix='content_by_category')
    def by_category(self, request):
        """Get contents grouped by category - optimized version with error handling"""
        try:
            # Import at method level to avoid circular imports
            from django.conf import settings
            from django.db import connection

            # Log query count in development
            if settings.DEBUG:
                initial_queries = len(connection.queries)
            # Optimize: Get user's custom categories only
            user_categories = Category.objects.filter(
                user=self.request.user
            ).only('id', 'name', 'slug', 'user')  # Only select needed fields
            
            # Optimize: Get all user's contents with category data prefetched
            user_contents = self.get_queryset()
            
            result = {}
            
            # Group contents by category efficiently using in-memory grouping
            contents_by_category = {}
            for content in user_contents:
                category_id = content.category_id if content.category else None
                if category_id not in contents_by_category:
                    contents_by_category[category_id] = []
                contents_by_category[category_id].append(content)
            
            # Build result for each category
            for category in user_categories:
                category_contents = contents_by_category.get(category.id, [])
                # Include all user's custom categories (even if empty)
                result[category.slug] = {
                    'category': CategorySerializer(category).data,
                    'contents': ContentSerializer(category_contents, many=True).data,
                    'count': len(category_contents)
                }
            
            # Add uncategorized content
            uncategorized_contents = contents_by_category.get(None, [])
            if uncategorized_contents:
                result['uncategorized'] = {
                    'category': {'name': '미분류', 'slug': 'uncategorized'},
                    'contents': ContentSerializer(uncategorized_contents, many=True).data,
                    'count': len(uncategorized_contents)
                }
            
            # Log performance metrics in development
            if settings.DEBUG:
                final_queries = len(connection.queries)
                query_count = final_queries - initial_queries
                logger.info(f"by_category API - Query count: {query_count}, Categories: {len(user_categories)}, Contents: {len(user_contents)}")
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error in by_category view: {str(e)}", exc_info=True)
            return Response(
                {'error': '카테고리별 콘텐츠 조회 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="콘텐츠 AI 검증",
        operation_description="학습 콘텐츠의 사실적 정확성, 논리적 일관성, 제목 적합성을 AI로 검증합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'content'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='콘텐츠 제목'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='콘텐츠 내용 (마크다운)'),
            }
        ),
        responses={
            200: openapi.Response(
                description="검증 완료",
                examples={
                    "application/json": {
                        "is_valid": True,
                        "factual_accuracy": {"score": 95, "issues": []},
                        "logical_consistency": {"score": 90, "issues": []},
                        "title_relevance": {"score": 100, "issues": []},
                        "overall_feedback": "훌륭한 학습 자료입니다."
                    }
                }
            ),
            400: "잘못된 요청"
        }
    )
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate content using AI"""
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()

        if not title or not content:
            return Response(
                {'error': '제목과 내용을 모두 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(content) < 200:
            return Response(
                {'error': '서술 평가는 최소 200자 이상의 콘텐츠가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = validate_content(title, content)
            return Response(result)
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': f'AI 검증 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="콘텐츠 AI 검증 및 저장",
        operation_description="기존 콘텐츠를 AI로 검증하고 결과를 DB에 저장합니다. 주간 시험 생성 시 필수입니다.",
        responses={
            200: openapi.Response(
                description="검증 성공",
                examples={
                    "application/json": {
                        "message": "AI 검증이 완료되었습니다.",
                        "is_valid": True,
                        "ai_validation_score": 95.0,
                        "validated_at": "2025-01-15T10:30:00Z"
                    }
                }
            ),
            400: "이미 검증된 콘텐츠 또는 잘못된 요청",
            500: "AI 검증 실패"
        }
    )
    @action(detail=True, methods=['post'])
    def validate_and_save(self, request, pk=None):
        """Validate content using AI and save results to DB"""
        from django.utils import timezone

        content_obj = self.get_object()

        # 이미 검증된 콘텐츠 체크
        if content_obj.is_ai_validated:
            return Response(
                {
                    'message': '이미 AI 검증이 완료된 콘텐츠입니다.',
                    'is_valid': True,
                    'ai_validation_score': content_obj.ai_validation_score,
                    'validated_at': content_obj.ai_validated_at
                },
                status=status.HTTP_200_OK
            )

        # 콘텐츠 길이 확인
        if len(content_obj.content.strip()) < 200:
            return Response(
                {'error': 'AI 검증은 최소 200자 이상의 콘텐츠가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # AI 검증 실행
            result = validate_content(content_obj.title, content_obj.content)

            # 검증 결과 저장
            if result.get('is_valid', False):
                # 평균 점수 계산
                scores = [
                    result['factual_accuracy']['score'],
                    result['logical_consistency']['score'],
                    result['title_relevance']['score']
                ]
                avg_score = sum(scores) / len(scores)

                # DB 업데이트
                content_obj.is_ai_validated = True
                content_obj.ai_validation_score = round(avg_score, 1)
                content_obj.ai_validation_result = result
                content_obj.ai_validated_at = timezone.now()
                content_obj.save()

                logger.info(f"Content {content_obj.id} AI validation saved: {avg_score}")

                return Response({
                    'message': 'AI 검증이 완료되었습니다.',
                    'is_valid': True,
                    'ai_validation_score': content_obj.ai_validation_score,
                    'validated_at': content_obj.ai_validated_at,
                    'result': result
                }, status=status.HTTP_200_OK)
            else:
                # 검증 실패 (점수 70 미만)
                return Response({
                    'message': 'AI 검증 결과 일부 개선이 필요합니다.',
                    'is_valid': False,
                    'result': result
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"AI validation failed for content {content_obj.id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'AI 검증 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )