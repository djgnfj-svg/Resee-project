from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from .models import Category, Tag, Content
from .serializers import CategorySerializer, TagSerializer, ContentSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """Category viewset"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        # Return global categories (user=None) and user's custom categories
        return Category.objects.filter(
            models.Q(user=None) | models.Q(user=self.request.user)
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """Tag viewset"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ContentViewSet(viewsets.ModelViewSet):
    """Content viewset"""
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'priority', 'tags']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Content.objects.filter(author=self.request.user)
        
        # Category filter
        category_slug = self.request.query_params.get('category_slug', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get contents grouped by category"""
        categories = Category.objects.all()
        result = {}
        
        for category in categories:
            contents = self.get_queryset().filter(category=category)
            result[category.slug] = {
                'category': CategorySerializer(category).data,
                'contents': ContentSerializer(contents, many=True).data,
                'count': contents.count()
            }
        
        # Add uncategorized content
        uncategorized = self.get_queryset().filter(category__isnull=True)
        result['uncategorized'] = {
            'category': {'name': '미분류', 'slug': 'uncategorized'},
            'contents': ContentSerializer(uncategorized, many=True).data,
            'count': uncategorized.count()
        }
        
        return Response(result)