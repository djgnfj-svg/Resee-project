from django.db import models


class LegalDocument(models.Model):
    """법적 문서 모델"""
    class DocumentType(models.TextChoices):
        PRIVACY_POLICY = 'privacy_policy', '개인정보처리방침'
        TERMS_OF_SERVICE = 'terms_of_service', '이용약관'
        REFUND_POLICY = 'refund_policy', '환불정책'
        COOKIE_POLICY = 'cookie_policy', '쿠키정책'
    
    title = models.CharField(max_length=200, help_text="문서 제목")
    document_type = models.CharField(
        max_length=50, 
        choices=DocumentType.choices,
        unique=True,
        help_text="문서 유형"
    )
    content = models.TextField(help_text="문서 내용")
    version = models.CharField(max_length=20, default='1.0', help_text="문서 버전")
    effective_date = models.DateTimeField(help_text="시행일")
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="활성 상태")
    
    class Meta:
        ordering = ['-effective_date']
        verbose_name = '법적 문서'
        verbose_name_plural = '법적 문서들'
    
    def __str__(self):
        return f"{self.get_document_type_display()} v{self.version}"


class UserConsent(models.Model):
    """사용자 동의 기록"""
    class ConsentType(models.TextChoices):
        PRIVACY_POLICY = 'privacy_policy', '개인정보처리방침'
        TERMS_OF_SERVICE = 'terms_of_service', '이용약관'
        MARKETING = 'marketing', '마케팅 정보 수신'
        COOKIES = 'cookies', '쿠키 사용'
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=50, choices=ConsentType.choices)
    document_version = models.CharField(max_length=20, help_text="동의한 문서 버전")
    
    # 동의 상태
    is_consented = models.BooleanField(default=False)
    consented_at = models.DateTimeField(auto_now_add=True)
    
    # IP 주소 기록 (GDPR 요구사항)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, help_text="브라우저 정보")
    
    class Meta:
        unique_together = ['user', 'consent_type', 'document_version']
        ordering = ['-consented_at']
        verbose_name = '사용자 동의'
        verbose_name_plural = '사용자 동의 기록'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_consent_type_display()} - {self.document_version}"


class DataDeletionRequest(models.Model):
    """데이터 삭제 요청 (GDPR 준수)"""
    class Status(models.TextChoices):
        PENDING = 'pending', '대기중'
        IN_PROGRESS = 'in_progress', '처리중'
        COMPLETED = 'completed', '완료'
        REJECTED = 'rejected', '거부'
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='deletion_requests')
    reason = models.TextField(blank=True, help_text="삭제 요청 사유")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # 처리 정보
    processed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_deletion_requests'
    )
    processed_at = models.DateTimeField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, help_text="관리자 메모")
    
    # 일시
    requested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = '데이터 삭제 요청'
        verbose_name_plural = '데이터 삭제 요청들'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_status_display()}"


class DataExportRequest(models.Model):
    """데이터 내보내기 요청 (GDPR 준수)"""
    class Status(models.TextChoices):
        PENDING = 'pending', '대기중'
        PROCESSING = 'processing', '처리중'
        READY = 'ready', '다운로드 준비완료'
        DOWNLOADED = 'downloaded', '다운로드 완료'
        EXPIRED = 'expired', '만료됨'
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='export_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # 파일 정보
    file_path = models.CharField(max_length=500, blank=True, help_text="생성된 파일 경로")
    expires_at = models.DateTimeField(blank=True, null=True, help_text="다운로드 링크 만료일")
    
    # 일시
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    downloaded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = '데이터 내보내기 요청'
        verbose_name_plural = '데이터 내보내기 요청들'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_status_display()}"


class CookieConsent(models.Model):
    """쿠키 동의 관리"""
    class CookieCategory(models.TextChoices):
        ESSENTIAL = 'essential', '필수 쿠키'
        ANALYTICS = 'analytics', '분석 쿠키'
        MARKETING = 'marketing', '마케팅 쿠키'
        FUNCTIONAL = 'functional', '기능 쿠키'
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='cookie_consents',
        blank=True,
        null=True
    )
    session_id = models.CharField(max_length=100, help_text="세션 ID (비회원용)")
    
    # 쿠키 카테고리별 동의
    essential_cookies = models.BooleanField(default=True, help_text="필수 쿠키 (항상 허용)")
    analytics_cookies = models.BooleanField(default=False, help_text="분석 쿠키")
    marketing_cookies = models.BooleanField(default=False, help_text="마케팅 쿠키")
    functional_cookies = models.BooleanField(default=False, help_text="기능 쿠키")
    
    # 메타데이터
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    consented_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-consented_at']
        verbose_name = '쿠키 동의'
        verbose_name_plural = '쿠키 동의 기록'
    
    def __str__(self):
        identifier = self.user.email if self.user else f"Session: {self.session_id[:10]}"
        return f"{identifier} - 쿠키 동의"