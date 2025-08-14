from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    # 법적 문서
    path('documents/', views.LegalDocumentListView.as_view(), name='document-list'),
    path('documents/<str:document_type>/', views.LegalDocumentDetailView.as_view(), name='document-detail'),
    
    # 사용자 동의
    path('consents/', views.UserConsentListView.as_view(), name='consent-list'),
    path('consents/create/', views.CreateConsentView.as_view(), name='consent-create'),
    path('consents/withdraw/', views.withdraw_consent, name='consent-withdraw'),
    
    # GDPR 권리
    path('gdpr/data-summary/', views.gdpr_data_summary, name='gdpr-data-summary'),
    path('gdpr/delete-request/', views.DataDeletionRequestView.as_view(), name='gdpr-delete-request'),
    path('gdpr/export-request/', views.DataExportRequestView.as_view(), name='gdpr-export-request'),
    path('gdpr/download/<int:request_id>/', views.DownloadDataExportView.as_view(), name='gdpr-download'),
    
    # 쿠키 동의
    path('cookies/', views.CookieConsentView.as_view(), name='cookie-consent'),
]