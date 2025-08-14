import json
import os
import tempfile
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LegalDocument, UserConsent, DataDeletionRequest, DataExportRequest, CookieConsent
from .serializers import (
    LegalDocumentSerializer, UserConsentSerializer, CreateConsentSerializer,
    DataDeletionRequestSerializer, DataExportRequestSerializer, CookieConsentSerializer,
    UpdateCookieConsentSerializer, GDPRDataExportSerializer
)
from .services import GDPRService


class LegalDocumentDetailView(generics.RetrieveAPIView):
    """법적 문서 조회"""
    serializer_class = LegalDocumentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'document_type'
    
    def get_queryset(self):
        return LegalDocument.objects.filter(is_active=True)


class LegalDocumentListView(generics.ListAPIView):
    """법적 문서 목록 조회"""
    serializer_class = LegalDocumentSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return LegalDocument.objects.filter(is_active=True).order_by('document_type')


class UserConsentListView(generics.ListAPIView):
    """사용자 동의 기록 조회"""
    serializer_class = UserConsentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserConsent.objects.filter(user=self.request.user).order_by('-consented_at')


class CreateConsentView(APIView):
    """동의 생성/업데이트"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateConsentSerializer(data=request.data)
        if serializer.is_valid():
            consent_type = serializer.validated_data['consent_type']
            is_consented = serializer.validated_data['is_consented']
            document_version = serializer.validated_data.get('document_version')
            
            # 최신 문서 버전 가져오기
            if not document_version:
                try:
                    document = LegalDocument.objects.get(
                        document_type=consent_type,
                        is_active=True
                    )
                    document_version = document.version
                except LegalDocument.DoesNotExist:
                    return Response(
                        {'error': '해당 문서를 찾을 수 없습니다.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # IP 주소 및 User Agent 수집
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 동의 기록 생성/업데이트
            consent, created = UserConsent.objects.update_or_create(
                user=request.user,
                consent_type=consent_type,
                document_version=document_version,
                defaults={
                    'is_consented': is_consented,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )
            
            serializer = UserConsentSerializer(consent)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DataDeletionRequestView(APIView):
    """데이터 삭제 요청 (GDPR Right to be Forgotten)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 기존 대기중인 요청 확인
        existing_request = DataDeletionRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_request:
            return Response(
                {'error': '이미 처리 중인 삭제 요청이 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DataDeletionRequestSerializer(data=request.data)
        if serializer.is_valid():
            deletion_request = serializer.save(user=request.user)
            
            # TODO: 이메일 알림 발송 (관리자에게)
            
            return Response(
                DataDeletionRequestSerializer(deletion_request).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """삭제 요청 상태 조회"""
        deletion_requests = DataDeletionRequest.objects.filter(user=request.user)
        serializer = DataDeletionRequestSerializer(deletion_requests, many=True)
        return Response(serializer.data)


class DataExportRequestView(APIView):
    """데이터 내보내기 요청 (GDPR Right to Data Portability)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 기존 대기중인 요청 확인
        existing_request = DataExportRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'processing']
        ).first()
        
        if existing_request:
            return Response(
                {'error': '이미 처리 중인 내보내기 요청이 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 새 요청 생성
        export_request = DataExportRequest.objects.create(user=request.user)
        
        # 백그라운드에서 데이터 내보내기 처리
        from .tasks import process_data_export
        process_data_export.delay(export_request.id)
        
        return Response(
            DataExportRequestSerializer(export_request).data,
            status=status.HTTP_201_CREATED
        )
    
    def get(self, request):
        """내보내기 요청 상태 조회"""
        export_requests = DataExportRequest.objects.filter(user=request.user)
        serializer = DataExportRequestSerializer(export_requests, many=True)
        return Response(serializer.data)


class DownloadDataExportView(APIView):
    """데이터 내보내기 파일 다운로드"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, request_id):
        try:
            export_request = DataExportRequest.objects.get(
                id=request_id,
                user=request.user,
                status='ready'
            )
        except DataExportRequest.DoesNotExist:
            raise Http404
        
        # 만료 확인
        if export_request.expires_at and timezone.now() > export_request.expires_at:
            export_request.status = 'expired'
            export_request.save()
            return Response(
                {'error': '다운로드 링크가 만료되었습니다.'},
                status=status.HTTP_410_GONE
            )
        
        # 파일 다운로드
        if not os.path.exists(export_request.file_path):
            return Response(
                {'error': '파일을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with open(export_request.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="resee_data_export_{request.user.id}.json"'
            
            # 다운로드 기록
            export_request.status = 'downloaded'
            export_request.downloaded_at = timezone.now()
            export_request.save()
            
            return response


class CookieConsentView(APIView):
    """쿠키 동의 관리"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """현재 쿠키 동의 상태 조회"""
        if request.user.is_authenticated:
            try:
                consent = CookieConsent.objects.filter(user=request.user).latest('consented_at')
                serializer = CookieConsentSerializer(consent)
                return Response(serializer.data)
            except CookieConsent.DoesNotExist:
                pass
        
        # 세션 기반 조회 (비회원)
        session_id = request.session.session_key
        if session_id:
            try:
                consent = CookieConsent.objects.filter(session_id=session_id).latest('consented_at')
                serializer = CookieConsentSerializer(consent)
                return Response(serializer.data)
            except CookieConsent.DoesNotExist:
                pass
        
        # 기본 동의 상태 반환
        return Response({
            'essential_cookies': True,
            'analytics_cookies': False,
            'marketing_cookies': False,
            'functional_cookies': False
        })
    
    def post(self, request):
        """쿠키 동의 설정"""
        serializer = UpdateCookieConsentSerializer(data=request.data)
        if serializer.is_valid():
            # 클라이언트 정보 수집
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 동의 기록 생성
            consent_data = {
                'essential_cookies': True,  # 항상 필수
                'analytics_cookies': serializer.validated_data['analytics_cookies'],
                'marketing_cookies': serializer.validated_data['marketing_cookies'],
                'functional_cookies': serializer.validated_data['functional_cookies'],
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            if request.user.is_authenticated:
                consent_data['user'] = request.user
            else:
                # 세션이 없으면 생성
                if not request.session.session_key:
                    request.session.create()
                consent_data['session_id'] = request.session.session_key
            
            consent = CookieConsent.objects.create(**consent_data)
            serializer = CookieConsentSerializer(consent)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gdpr_data_summary(request):
    """GDPR 데이터 요약 정보"""
    user = request.user
    
    summary = {
        'personal_data': {
            'email': user.email,
            'account_created': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'email_verified': user.is_email_verified
        },
        'data_usage': {
            'contents_created': user.contents.count(),
            'reviews_completed': user.review_histories.count(),
            'ai_questions_generated': getattr(user, 'ai_usage_records', None) and 
                                    user.ai_usage_records.aggregate(
                                        total=models.Sum('usage_count')
                                    )['total'] or 0
        },
        'consents': [
            {
                'type': consent.consent_type,
                'version': consent.document_version,
                'consented': consent.is_consented,
                'date': consent.consented_at.isoformat()
            }
            for consent in user.consents.all()
        ],
        'rights': {
            'data_portability': True,
            'right_to_be_forgotten': True,
            'consent_withdrawal': True,
            'data_rectification': True
        }
    }
    
    return Response(summary)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_consent(request):
    """동의 철회"""
    consent_type = request.data.get('consent_type')
    
    if not consent_type:
        return Response(
            {'error': 'consent_type이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 필수 동의는 철회 불가
    if consent_type in ['privacy_policy', 'terms_of_service']:
        return Response(
            {'error': '필수 동의 항목은 철회할 수 없습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        consent = UserConsent.objects.filter(
            user=request.user,
            consent_type=consent_type,
            is_consented=True
        ).latest('consented_at')
        
        # 동의 철회 기록 생성
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserConsent.objects.create(
            user=request.user,
            consent_type=consent_type,
            document_version=consent.document_version,
            is_consented=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response({'message': '동의가 철회되었습니다.'})
        
    except UserConsent.DoesNotExist:
        return Response(
            {'error': '철회할 동의를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )