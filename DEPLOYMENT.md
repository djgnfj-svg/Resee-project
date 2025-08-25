# 🚀 Resee 배포 가이드

## 📋 목차
- [베타 배포](#베타-배포)
- [환경 설정](#환경-설정)
- [배포 스크립트](#배포-스크립트)
- [문제 해결](#문제-해결)

## 🏗️ 베타 배포

### 1. 사전 준비
```bash
# 필수 요구사항
- Docker & Docker Compose
- Git
- curl (헬스체크용)

# 환경변수 파일 설정
cp .env.example .env.beta
# .env.beta 파일 편집 필수!
```

### 2. 환경변수 설정
`.env.beta` 파일에서 다음 항목들을 반드시 설정하세요:

#### 필수 설정
- `SECRET_KEY`: Django 비밀키
- `DB_*`: 데이터베이스 연결 정보
- `ANTHROPIC_API_KEY`: Claude AI API 키
- `EMAIL_*`: 이메일 서비스 설정
- `GOOGLE_OAUTH2_*`: Google 로그인 설정

#### 권장 설정
- `SLACK_WEBHOOK_URL`: 알림용 Slack 웹훅
- `ALERT_EMAIL_RECIPIENTS`: 시스템 알림 수신자

### 3. 배포 실행

#### 전체 배포 (품질검사 포함)
```bash
chmod +x deploy-beta.sh
./deploy-beta.sh
```

#### 빠른 배포 (테스트 스킵)
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

### 4. 배포 프로세스

배포 스크립트는 다음 단계를 수행합니다:

1. **필수 요구사항 확인**
   - Docker, Docker Compose 설치 확인
   - 환경변수 파일 존재 확인

2. **Git 상태 확인**
   - 커밋되지 않은 변경사항 알림
   - 현재 브랜치 정보 표시

3. **코드 품질 검사** (선택적)
   - 백엔드 테스트 실행
   - 프론트엔드 테스트 실행
   - 코드 형식 검사 (Black, Flake8, ESLint)

4. **이미지 빌드**
   - 기존 컨테이너 정리
   - 새 Docker 이미지 빌드

5. **베타 환경 배포**
   - 서비스 시작
   - 데이터베이스 마이그레이션
   - 정적 파일 수집

6. **헬스체크**
   - 백엔드/프론트엔드 서비스 상태 확인
   - 최대 30회 시도 (2.5분)

7. **배포 정보 출력**
   - 서비스 URL 및 관리 명령어 안내

## 🔧 배포 후 관리

### 서비스 상태 확인
```bash
# 컨테이너 상태
docker-compose ps

# 서비스 로그
docker-compose logs -f

# 헬스체크
curl http://localhost:8000/health/
curl http://localhost:3000/
```

### 주요 관리 명령어
```bash
# 서비스 중단
docker-compose down

# 서비스 재시작
docker-compose restart

# 특정 서비스 재시작
docker-compose restart backend
docker-compose restart frontend

# 로그 실시간 확인
docker-compose logs -f backend
docker-compose logs -f celery
```

### 데이터베이스 관리
```bash
# 마이그레이션
docker-compose exec backend python manage.py migrate

# Django shell
docker-compose exec backend python manage.py shell_plus

# 관리자 계정 생성
docker-compose exec backend python manage.py createsuperuser
```

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. 서비스 시작 실패
```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 포트 충돌 확인
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# 컨테이너 재시작
docker-compose restart
```

#### 2. 데이터베이스 연결 오류
```bash
# 환경변수 확인
docker-compose exec backend env | grep DB_

# 데이터베이스 연결 테스트
docker-compose exec backend python manage.py dbshell
```

#### 3. AI 서비스 오류
```bash
# API 키 확인
docker-compose exec backend env | grep ANTHROPIC

# AI 서비스 로그 확인
docker-compose logs backend | grep -i anthropic
```

#### 4. 이메일 발송 실패
```bash
# 이메일 설정 확인
docker-compose exec backend python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
"
```

### 롤백 방법
```bash
# 현재 배포 중단
docker-compose down

# 이전 버전으로 롤백
git checkout <previous-commit>
./deploy-beta.sh
```

### 로그 분석
```bash
# 에러 로그 필터링
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error

# 특정 시간대 로그
docker-compose logs --since="2024-01-01T10:00:00" backend

# 로그 파일로 저장
docker-compose logs > deployment.log
```

## 📊 모니터링

### 서비스 URL
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin/
- **헬스체크**: http://localhost:8000/health/

### 시스템 모니터링
```bash
# 리소스 사용량
docker stats

# 디스크 사용량
docker system df

# 메모리 사용량
docker-compose exec backend free -h
```

## 🔐 보안 고려사항

### 환경변수 보안
- `.env.beta` 파일을 절대 커밋하지 마세요
- 강력한 SECRET_KEY 사용
- 데이터베이스 비밀번호 정기 변경

### 네트워크 보안
- 프로덕션에서는 HTTPS 사용 필수
- 방화벽 설정으로 필요한 포트만 개방
- Redis/PostgreSQL 외부 접근 제한

### API 보안
- Rate limiting 활성화
- CORS 설정 검토
- JWT 토큰 만료 시간 적절히 설정

## 📞 지원

배포 관련 문제가 발생하면:
1. 이 문서의 [문제 해결](#문제-해결) 섹션 확인
2. 로그 분석으로 원인 파악
3. GitHub Issues에 버그 리포트

---
*이 가이드는 Resee v1.0 베타 배포용으로 작성되었습니다.*