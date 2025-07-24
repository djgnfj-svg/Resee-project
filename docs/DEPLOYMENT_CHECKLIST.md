# 📋 Resee 배포 체크리스트

이 문서는 Resee 프로젝트를 프로덕션 환경에 배포하기 전 확인해야 할 모든 사항을 담고 있습니다.

## 🚀 배포 전 필수 확인사항

### 1. 환경 변수 및 보안 설정 ⚠️ 

#### 1.1 환경 변수 파일 생성
- [ ] `.env.production` 파일 생성 완료
- [ ] `.gitignore`에 `.env.production` 추가 확인
- [ ] 모든 시크릿 값들이 실제 프로덕션 값으로 변경되었는지 확인

#### 1.2 필수 환경 변수 설정
```bash
# Django 설정
- [ ] SECRET_KEY: 새로운 키 생성 (django.core.management.utils.get_random_secret_key() 사용)
- [ ] DEBUG: False
- [ ] ALLOWED_HOSTS: 실제 도메인 입력 (예: example.com,www.example.com)
- [ ] ENVIRONMENT: production

# 데이터베이스
- [ ] DATABASE_URL: postgresql://[실제사용자]:[실제비밀번호]@db:5432/[실제DB명]

# Redis & Celery
- [ ] REDIS_URL: redis://redis:6379/0
- [ ] CELERY_BROKER_URL: amqp://[실제사용자]:[실제비밀번호]@rabbitmq:5672//
- [ ] CELERY_RESULT_BACKEND: redis://redis:6379/0

# Google OAuth 2.0
- [ ] GOOGLE_OAUTH2_CLIENT_ID: Google Console에서 발급받은 ID
- [ ] GOOGLE_OAUTH2_CLIENT_SECRET: Google Console에서 발급받은 Secret

# AI 서비스 (Claude)
- [ ] ANTHROPIC_API_KEY: Anthropic에서 발급받은 API 키

# 이메일 서비스
- [ ] EMAIL_BACKEND: django_ses.SESBackend (또는 SMTP)
- [ ] AWS_ACCESS_KEY_ID: AWS IAM 키 (SES 사용시)
- [ ] AWS_SECRET_ACCESS_KEY: AWS IAM Secret (SES 사용시)
- [ ] DEFAULT_FROM_EMAIL: noreply@yourdomain.com
```

### 2. Docker 및 배포 설정 🐳

#### 2.1 Docker 파일 확인
- [ ] `docker-compose.production.yml` 파일 생성/확인
- [ ] `Dockerfile` 프로덕션 최적화 확인
- [ ] `.dockerignore` 파일 확인 (불필요한 파일 제외)

#### 2.2 Nginx 설정
- [ ] `nginx.conf` 파일 생성
- [ ] SSL 인증서 경로 설정
- [ ] 정적 파일 경로 설정
- [ ] 프록시 설정 확인

```nginx
# nginx.conf 예시
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # 보안 헤더들...
}
```

### 3. 데이터베이스 설정 🗄️

- [ ] 프로덕션 PostgreSQL 데이터베이스 생성
- [ ] 데이터베이스 사용자 및 권한 설정
- [ ] 마이그레이션 파일 최신화 확인
- [ ] 초기 데이터 스크립트 준비 (카테고리, AI 질문 타입 등)
- [ ] 백업 정책 수립 (일일/주간/월간)

### 4. 도메인 및 SSL 설정 🌐

- [ ] 도메인 구매 완료
- [ ] DNS A 레코드 설정 (서버 IP 연결)
- [ ] DNS CNAME 설정 (www 서브도메인)
- [ ] Let's Encrypt SSL 인증서 발급
- [ ] SSL 자동 갱신 크론탭 설정
- [ ] HTTPS 강제 리다이렉트 설정

### 5. 서버 보안 설정 🔐

#### 5.1 방화벽 설정
- [ ] SSH (22번 포트) - 특정 IP만 허용
- [ ] HTTP (80번 포트) - 모두 허용
- [ ] HTTPS (443번 포트) - 모두 허용
- [ ] 기타 포트 모두 차단

#### 5.2 Django 보안 설정
- [ ] `python manage.py check --deploy` 실행 및 경고사항 해결
- [ ] SECURE_SSL_REDIRECT = True
- [ ] SESSION_COOKIE_SECURE = True
- [ ] CSRF_COOKIE_SECURE = True
- [ ] SECURE_BROWSER_XSS_FILTER = True
- [ ] SECURE_CONTENT_TYPE_NOSNIFF = True
- [ ] X_FRAME_OPTIONS = 'DENY'

### 6. 정적 파일 및 미디어 설정 📁

- [ ] STATIC_ROOT 설정 확인
- [ ] MEDIA_ROOT 설정 확인
- [ ] `python manage.py collectstatic` 실행 확인
- [ ] WhiteNoise 설정 (또는 CDN 설정)
- [ ] 업로드 파일 크기 제한 설정

### 7. 모니터링 및 로깅 📊

#### 7.1 로깅 설정
- [ ] 로그 파일 저장 경로 설정
- [ ] 로그 로테이션 설정
- [ ] 에러 로그 알림 설정 (이메일/Slack)
- [ ] Sentry 또는 유사 서비스 연동

#### 7.2 모니터링 설정
- [ ] 서버 리소스 모니터링 (CPU, 메모리, 디스크)
- [ ] 애플리케이션 성능 모니터링
- [ ] 데이터베이스 쿼리 모니터링
- [ ] 헬스체크 엔드포인트 설정

### 8. 백업 및 복구 💾

- [ ] PostgreSQL 자동 백업 스크립트 설정
- [ ] Redis 백업 설정
- [ ] 미디어 파일 백업 설정
- [ ] 백업 파일 원격 저장소 전송 설정
- [ ] 복구 절차 문서화 및 테스트

### 9. 성능 최적화 ⚡

- [ ] Gunicorn worker 수 최적화 (CPU 코어 수 * 2 + 1)
- [ ] PostgreSQL 연결 풀링 설정
- [ ] Redis 메모리 제한 설정
- [ ] 데이터베이스 인덱스 최적화
- [ ] 프론트엔드 빌드 최적화 (압축, 코드 스플리팅)

### 10. 배포 프로세스 🔄

#### 10.1 배포 전 로컬 테스트
```bash
# 프로덕션 환경 로컬 테스트
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up

# Django 체크
docker exec resee-backend python manage.py check --deploy
docker exec resee-backend python manage.py test
```

#### 10.2 실제 배포 순서
1. [ ] 현재 서비스 백업
2. [ ] 새 버전 이미지 빌드
3. [ ] 데이터베이스 마이그레이션
4. [ ] 정적 파일 수집
5. [ ] 서비스 재시작
6. [ ] 헬스체크 확인

### 11. 배포 후 확인사항 ✅

#### 11.1 기능 테스트
- [ ] 홈페이지 접속 확인
- [ ] 회원가입 프로세스 테스트
- [ ] 로그인/로그아웃 테스트
- [ ] Google OAuth 로그인 테스트
- [ ] 콘텐츠 생성/수정/삭제 테스트
- [ ] 복습 기능 테스트
- [ ] AI 질문 생성 테스트

#### 11.2 성능 및 보안 확인
- [ ] HTTPS 인증서 확인 (https://www.ssllabs.com/ssltest/)
- [ ] 페이지 로딩 속도 측정
- [ ] 에러 로그 확인
- [ ] 리소스 사용률 확인

### 12. 롤백 계획 🔙

- [ ] 이전 버전 Docker 이미지 태그 기록
- [ ] 데이터베이스 백업 파일 위치 확인
- [ ] 롤백 스크립트 준비
- [ ] 롤백 절차 문서화

---

## 📝 추가 참고사항

### 시크릿 키 생성 방법
```python
# Django shell에서
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 유용한 명령어 모음
```bash
# 로그 확인
docker-compose logs -f backend

# Django 관리 명령
docker exec resee-backend python manage.py [명령어]

# 데이터베이스 백업
docker exec resee-db pg_dump -U resee_user resee_db > backup_$(date +%Y%m%d).sql

# SSL 인증서 갱신
certbot renew --nginx
```

### 문제 해결 가이드
- 502 Bad Gateway: 백엔드 서비스 확인
- 정적 파일 404: collectstatic 실행 확인
- 데이터베이스 연결 실패: 환경 변수 및 네트워크 확인

---

**작성일**: 2024-01-24  
**최종 수정일**: 2024-01-24  
**버전**: 1.0