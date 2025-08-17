from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ContentViewSet

app_name = 'content'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'contents', ContentViewSet, basename='contents')

urlpatterns = [
    path('', include(router.urls)),
]