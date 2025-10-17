# 보안 정책

## 지원 버전

| 버전 | 지원 여부 |
| ------- | ------------------ |
| 1.0.x   | ✅ 지원 |
| < 1.0   | ❌ 미지원 |

## 보안 기능

### 1. 인증 및 권한
- **JWT 토큰 기반 인증**: Access + Refresh 토큰
- **토큰 만료**: Access 토큰은 1시간 후 만료
- **토큰 갱신**: 401 응답 시 자동 갱신
- **비밀번호 보안**: Django PBKDF2 알고리즘 (870,000회 반복)
- **세션 보안**: Secure, HttpOnly, SameSite 쿠키

### 2. 데이터 보호
- **HTTPS 강제**: 모든 프로덕션 트래픽 HTTPS (CloudFlare)
- **CSRF 보호**: 모든 상태 변경 작업에 Django CSRF 토큰
- **XSS 보호**: React 자동 이스케이핑, Content-Security-Policy 헤더
- **SQL Injection 방어**: Django ORM 기본 방어

### 3. Rate Limiting
- **Redis 기반 제한**:
  - 익명 사용자: 100 요청/시간
  - 인증된 사용자: 1000 요청/시간
  - 로그인 시도: 5 요청/분
- **DDoS 방어**: CloudFlare WAF

### 4. 보안 헤더
```python
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
```

### 5. 이메일 보안
- **이메일 인증**: 신규 계정에 필수
- **SHA-256 토큰 해싱**: 이메일 인증 토큰 DB에 해시 저장
- **상수 시간 비교**: 타이밍 공격 방지
- **토큰 만료**: 인증 토큰은 24시간 후 만료

## 환경 변수 보안

### ⚠️ 중요: Git에 민감한 데이터 절대 커밋 금지

**필수 환경 변수**:
```bash
# .env.example을 템플릿으로 사용
cp .env.example .env

# 절대 커밋하지 말 것:
# - .env
# - .env.prod
# - .env.local
```

### 보호해야 할 민감한 변수:
- `SECRET_KEY`: Django 비밀 키 (생성: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- `ANTHROPIC_API_KEY`: AI 서비스 API 키
- `SLACK_WEBHOOK_URL`: Slack 웹훅 알림용
- `EMAIL_HOST_PASSWORD`: 이메일 서비스 비밀번호
- `GOOGLE_OAUTH2_CLIENT_SECRET`: OAuth 비밀키
- `ADMIN_PASSWORD`: 관리자 계정 비밀번호
- `TOSS_SECRET_KEY`: 결제 게이트웨이 비밀키

### 프로덕션 체크리스트:
- [ ] 프로덕션용 새로운 `SECRET_KEY` 생성
- [ ] `DEBUG=False` 설정
- [ ] `ALLOWED_HOSTS`에 실제 도메인 설정
- [ ] 강력한 비밀번호 사용 (최소 12자, 영문+숫자+특수문자)
- [ ] `ENFORCE_EMAIL_VERIFICATION=True` 활성화
- [ ] HTTPS 전용 쿠키 설정
- [ ] CloudFlare SSL/TLS 설정

## 의존성 보안

### 정기 업데이트
```bash
# Backend
pip install --upgrade pip
pip list --outdated

# Frontend
npm outdated
npm update
```

### 제거된 패키지 (v1.0)
보안/유지보수 이유로 제거된 패키지:
- `stripe`: Stripe 미사용 (Toss Payments 사용)
- `django-ses`: Gmail SMTP 사용
- `boto3`, `django-storages`: AWS S3 미사용
- `django-allauth`, `dj-rest-auth`: 과도한 의존성, 단순 JWT 사용

### 개발 의존성
`requirements-dev.txt`로 분리:
- `django-debug-toolbar`: 디버그 툴바 (개발 전용)

## 알려진 이슈

### 현재 제한사항
1. **테스트 실패**: `test_token_blacklisted_on_password_change` - JWT 블랙리스트 미구현
   - **영향도**: Medium
   - **임시 대응**: 토큰은 1시간 후 자동 만료
   - **수정 계획**: v1.1에서 구현 예정

## 취약점 신고

보안 취약점을 발견하신 경우 이메일로 연락주세요:
**djgnfj8923@naver.com**

**보안 취약점은 절대 공개 GitHub 이슈로 생성하지 마세요.**

### 신고 시 포함할 내용:
1. 취약점 설명
2. 재현 단계
3. 잠재적 영향
4. 수정 제안 (가능한 경우)

### 응답 일정:
- **최초 응답**: 48시간 이내
- **상태 업데이트**: 1주일 이내
- **수정 일정**: 심각도별 (Critical: 1-3일, High: 1주, Medium: 2주)

## 기여자를 위한 보안 모범 사례

### 코드 리뷰 체크리스트:
- [ ] 하드코딩된 자격증명 없음
- [ ] 모든 사용자 입력에 대한 검증
- [ ] SQL 쿼리는 ORM 또는 파라미터화된 쿼리 사용
- [ ] eval() 또는 exec() 미사용
- [ ] 파일 업로드 검증 및 정제
- [ ] 보호된 엔드포인트에 인증 필수
- [ ] 부하가 큰 작업에 Rate limiting 적용

### 테스트:
```bash
# 보안 테스트 실행
docker-compose exec backend python -m pytest accounts/tests/test_security.py

# 일반적인 취약점 확인
docker-compose exec backend python manage.py check --deploy
```

## 보안 사고 대응

### 보안 침해 발생 시:
1. **즉시 조치**:
   - 모든 비밀키 교체 (SECRET_KEY, API 키)
   - 모든 사용자 강제 로그아웃 (JWT 토큰 무효화)
   - 유지보수 모드 활성화
   - 영향받은 사용자에게 알림

2. **조사**:
   - 로그 확인: `/backend/logs/security.log`
   - Slack 알림 검토
   - 공격 패턴 분석

3. **복구**:
   - 취약점 패치
   - 필요시 백업에서 복구
   - 지속적인 공격 모니터링

## 모니터링 및 알림

### Slack 알림:
- Health check 실패
- 데이터베이스 연결 오류
- Redis 연결 오류
- 결제 실패 (>10건/시간)
- API 에러율 >5%
- Celery 큐 길이 >100

### 로그 파일:
- `backend/logs/django.log`: 일반 애플리케이션 로그
- `backend/logs/django_error.log`: 에러 로그만
- `backend/logs/security.log`: 보안 관련 이벤트
- `backend/logs/celery.log`: 백그라운드 작업 로그

## 규정 준수

### GDPR 준수:
- 사용자 데이터 삭제: `/api/accounts/delete-account/`
- 데이터 내보내기: 고객 지원 문의
- 개인정보 처리방침: `/privacy`
- 이용약관: `/terms`

### 데이터 보관:
- 사용자 데이터: 계정 삭제 시까지
- 로그: 30일 (순환)
- 백업: 30일
- 이메일 토큰: 24시간

---

**최종 업데이트**: 2025-10-17  
**버전**: 1.0
