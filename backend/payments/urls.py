from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # 결제 플랜
    path('plans/', views.PaymentPlanListView.as_view(), name='payment-plans'),
    
    # 일회성 결제
    path('create-payment-intent/', views.CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    
    # 구독 관리
    path('create-subscription/', views.CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscription/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscription/update/', views.UpdateSubscriptionView.as_view(), name='update-subscription'),
    path('subscription/cancel/', views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/status/', views.subscription_status, name='subscription-status'),
    path('subscription/preview-change/', views.preview_subscription_change, name='preview-subscription-change'),
    
    # 결제 기록
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    
    # Stripe 웹훅
    path('webhook/', views.stripe_webhook, name='stripe-webhook'),
]