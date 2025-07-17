from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, ContentViewSet
from .image_views import upload_image, delete_image

app_name = 'content'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'contents', ContentViewSet, basename='contents')

urlpatterns = [
    path('', include(router.urls)),
    path('upload-image/', upload_image, name='upload-image'),
    path('delete-image/<str:filename>/', delete_image, name='delete-image'),
]