from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, ContentViewSet
from .image_views import upload_image, delete_image

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'contents', ContentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload-image/', upload_image, name='upload_image'),
    path('delete-image/<str:filename>/', delete_image, name='delete_image'),
]