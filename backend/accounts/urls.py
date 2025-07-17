from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProfileView, PasswordChangeView, AccountDeleteView

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
]