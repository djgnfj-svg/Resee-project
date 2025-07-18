from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Category, Content
from .serializers import CategorySerializer, ContentSerializer
import logging

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    📂 카테고리 관리
    
    학습 콘텐츠를 분류하기 위한 카테고리를 관리합니다.
    전역 카테고리와 사용자별 커스텀 카테고리를 지원합니다.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        # Return global categories (user=None) and user's custom categories
        return Category.objects.filter(
            models.Q(user=None) | models.Q(user=self.request.user)
        )
    
    @swagger_auto_schema(
        operation_summary="카테고리 목록 조회",
        operation_description="사용자가 접근 가능한 모든 카테고리 목록을 반환합니다. (전역 + 개인 카테고리)",
        responses={200: CategorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="새 카테고리 생성",
        operation_description="사용자별 커스텀 카테고리를 생성합니다.",
        request_body=CategorySerializer,
        responses={201: CategorySerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class ContentViewSet(viewsets.ModelViewSet):
    """
    📖 학습 콘텐츠 관리
    
    사용자의 학습 콘텐츠를 생성, 수정, 삭제, 조회할 수 있습니다.
    필터링, 정렬 기능을 지원합니다.
    """
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'priority']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Content.objects.filter(author=self.request.user)
        
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
            openapi.Parameter('priority', openapi.IN_QUERY, description="우선순위로 필터링 (high/medium/low)", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="정렬 (-created_at, title, updated_at)", type=openapi.TYPE_STRING),
        ],
        responses={200: ContentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="새 콘텐츠 생성",
        operation_description="새로운 학습 콘텐츠를 생성합니다. 자동으로 복습 스케줄이 생성됩니다.",
        request_body=ContentSerializer,
        responses={201: ContentSerializer()}
    )
    def create(self, request, *args, **kwargs):
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
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
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
    def by_category(self, request):
        """Get contents grouped by category - optimized version with error handling"""
        try:
            # Get user-accessible categories with user filtering
            user_categories = Category.objects.filter(
                models.Q(user=None) | models.Q(user=self.request.user)
            )
            
            # Get all user's contents with category data in one query using select_related
            user_contents = self.get_queryset().select_related('category')
            
            result = {}
            
            # Group contents by category efficiently
            for category in user_categories:
                category_contents = [content for content in user_contents if content.category_id == category.id]
                if category_contents or category.user == self.request.user:  # Include user's custom categories even if empty
                    result[category.slug] = {
                        'category': CategorySerializer(category).data,
                        'contents': ContentSerializer(category_contents, many=True).data,
                        'count': len(category_contents)
                    }
            
            # Add uncategorized content
            uncategorized_contents = [content for content in user_contents if content.category is None]
            if uncategorized_contents:
                result['uncategorized'] = {
                    'category': {'name': '미분류', 'slug': 'uncategorized'},
                    'contents': ContentSerializer(uncategorized_contents, many=True).data,
                    'count': len(uncategorized_contents)
                }
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error in by_category view: {str(e)}", exc_info=True)
            return Response(
                {'error': '카테고리별 콘텐츠 조회 중 오류가 발생했습니다.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )