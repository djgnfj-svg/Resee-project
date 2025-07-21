# 향후 개선 사항 (Future Improvements)

## 🔐 회원가입 & 이메일 인증 개선

### 우선순위: 중간
### 예상 작업 시간: 2-3시간

#### 현재 상태:
- ✅ 이메일 인증 시스템 완전 구현됨 (백엔드 + 프론트엔드)
- ✅ 비밀번호 확인 검증 수정됨
- ⚠️ 현재 개발환경에서는 console backend 사용 (실제 이메일 발송 안됨)

#### 향후 작업 예정:
1. **실제 이메일 서비스 연동**
   - AWS SES 또는 SendGrid 설정
   - 도메인 인증 (SPF, DKIM, DMARC)
   - 프로덕션 환경 변수 설정

2. **이메일 발송 최적화**
   - 재시도 로직 강화 (현재 구현됨, 테스트 필요)
   - 이메일 템플릿 반응형 개선
   - 다국어 지원 (한국어/영어)

3. **사용자 경험 개선**
   - 이메일 인증 페이지 디자인 개선
   - 인증 완료 후 자동 로그인
   - 소셜 로그인 추가 (구글, 네이버, 카카오)

4. **보안 강화**
   - JWT 기반 토큰으로 변경 고려
   - 브루트포스 공격 방지
   - CAPTCHA 추가

5. **모니터링 & 분석**
   - 이메일 전달률 추적
   - 회원가입 전환율 분석
   - 이메일 인증 완료율 통계

#### 관련 파일:
- `backend/accounts/models.py` - 이메일 인증 필드
- `backend/accounts/views.py` - 인증 API 엔드포인트
- `backend/accounts/tasks.py` - Celery 이메일 태스크
- `backend/accounts/middleware.py` - 미인증 사용자 제한
- `frontend/src/pages/EmailVerificationPage.tsx`
- `frontend/src/pages/VerificationPendingPage.tsx`
- `backend/templates/accounts/email_verification.html`

#### 기술 부채:
- 현재 이메일 인증은 개발용 설정 (console backend)
- 프로덕션 환경에서 실제 이메일 서비스 설정 필요
- 이메일 발송 실패 시 사용자 알림 부족

---

## 📝 기타 개선 사항

### 우선순위: 낮음
- [ ] 비밀번호 재설정 기능
- [ ] 프로필 사진 업로드
- [ ] 계정 삭제 확인 프로세스 개선
- [ ] 사용자 활동 로그

---

**작성일**: 2025-07-21
**마지막 업데이트**: 2025-07-21