# Resee 배포 가이드 (AWS EC2)

## 📋 사전 준비

### 1. AWS 리소스 (이미 준비됨)
- ✅ EC2 인스턴스 (Ubuntu)
- ✅ 탄력적 IP 연결
- ✅ Route53 DNS 설정 (reseeall.com)
- ✅ 보안 그룹 포트 오픈: 80, 443

### 2. 필요한 정보
- `SECRET_KEY` - Django 시크릿 키
- `EMAIL_HOST_PASSWORD` - Gmail 앱 비밀번호
- `ANTHROPIC_API_KEY` - AI 기능용 (선택)

---

## 🚀 배포 절차

### Step 1: EC2 접속
```bash
ssh -i your-key.pem ubuntu@reseeall.com
```

### Step 2: 프로젝트 클론 (최초 1회)
```bash
git clone https://github.com/your-username/Resee-project.git
cd Resee-project
```

### Step 3: 환경변수 설정
```bash
# .env.prod 파일 확인 (이미 있음)
nano .env.prod

# 필수 확인 사항:
# - SECRET_KEY 설정됨
# - EMAIL_HOST_PASSWORD 설정됨
# - ALLOWED_HOSTS=reseeall.com,www.reseeall.com
# - ANTHROPIC_API_KEY 설정됨 (AI 기능 사용 시)
```

### Step 4: 배포 실행
```bash
chmod +x deploy.sh
./deploy.sh
```

**배포 시간**: 5-10분 소요

**자동 수행 작업**:
1. Docker 설치 확인
2. 환경변수 검증
3. 서비스 빌드 및 시작 (Backend → Redis → Celery → Frontend → Nginx)
4. 데이터베이스 마이그레이션
5. 정적 파일 수집

---

## ✅ 배포 확인

### 1. 서비스 상태 확인
```bash
docker-compose -f docker-compose.prod.yml ps
```

**모든 서비스가 "Up" 상태여야 함**:
- postgres
- redis
- backend
- celery
- celery-beat
- frontend
- nginx

### 2. 웹사이트 접속
```
https://reseeall.com
```

### 3. API 헬스체크
```bash
curl https://reseeall.com/api/health/
# 출력: {"status":"healthy","timestamp":...}

# 상세 헬스체크
curl https://reseeall.com/api/health/detailed/
```

### 4. 로그 확인
```bash
# 전체 로그
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs backend -f
docker-compose -f docker-compose.prod.yml logs celery -f
docker-compose -f docker-compose.prod.yml logs nginx -f
```

---

## 🔄 업데이트 배포

### 코드 업데이트
```bash
cd /home/ubuntu/Resee-project  # 또는 프로젝트 경로
git pull origin main
./deploy.sh
```

### 환경변수만 변경
```bash
nano .env.prod
docker-compose -f docker-compose.prod.yml restart
```

---

## 🐛 트러블슈팅

### 문제 1: 서비스가 시작되지 않음
```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs [service-name] --tail=50

# 일반적인 원인:
# - 메모리 부족 → deploy.sh가 자동으로 Swap 추가
# - 포트 충돌 → sudo lsof -i :80
# - 환경변수 오류 → .env.prod 확인
```

### 문제 2: 이메일 발송 실패
```bash
# Celery worker 상태 확인
docker-compose -f docker-compose.prod.yml logs celery -f

# 이메일 설정 확인
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

### 문제 3: 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# 데이터베이스 접속 테스트
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### 문제 4: AI 기능 작동 안 함
```bash
# ANTHROPIC_API_KEY 확인
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from django.conf import settings
>>> print(settings.ANTHROPIC_API_KEY)

# API 키가 없으면 .env.prod에 추가 후 재시작
```

### 문제 5: 정적 파일 로딩 실패
```bash
# 정적 파일 재수집
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Nginx 재시작
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 🛑 서비스 중지

### 일시 중지
```bash
docker-compose -f docker-compose.prod.yml stop
```

### 완전 종료 (데이터 유지)
```bash
docker-compose -f docker-compose.prod.yml down
```

### 완전 삭제 (데이터 포함)
```bash
docker-compose -f docker-compose.prod.yml down -v
# ⚠️ 경고: 데이터베이스 데이터도 삭제됨!
```

---

## 📊 모니터링

### 디스크 사용량
```bash
df -h
```

### 메모리 사용량
```bash
free -h
```

### Docker 리소스 확인
```bash
docker stats
```

### 로그 크기 확인
```bash
docker-compose -f docker-compose.prod.yml exec backend du -sh /app/logs
```

---

## 🔐 보안 체크리스트

- [ ] `.env.prod` 파일 권한 확인: `chmod 600 .env.prod`
- [ ] PostgreSQL 포트 외부 비노출 (docker-compose.prod.yml에서 제거됨)
- [ ] 방화벽 설정: 80, 443만 오픈
- [ ] SSH 키 기반 인증 사용
- [ ] 정기 백업 설정

---

## 📞 문제 해결 순서

1. **로그 확인** → `docker-compose -f docker-compose.prod.yml logs`
2. **헬스체크** → `curl https://reseeall.com/api/health/detailed/`
3. **서비스 재시작** → `docker-compose -f docker-compose.prod.yml restart [service]`
4. **완전 재배포** → `./deploy.sh`

---

## 🎯 빠른 명령어 참조

```bash
# 배포
./deploy.sh

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 재시작
docker-compose -f docker-compose.prod.yml restart

# 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 헬스체크
curl https://reseeall.com/api/health/detailed/
```
