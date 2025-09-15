# 🚀 Resee 운영 환경 배포 체크리스트

## ⚡ 즉시 확인 필수 사항

### 🔐 보안 설정 (CRITICAL)
- [ ] `.env.prod` 파일에서 모든 기본값 변경
  - [ ] `SECRET_KEY`: 50자 이상 랜덤 문자열
  - [ ] `POSTGRES_PASSWORD`: 강력한 데이터베이스 비밀번호
  - [ ] `REDIS_PASSWORD`: 강력한 Redis 비밀번호
  - [ ] `ANTHROPIC_API_KEY`: 실제 Claude API 키
- [ ] `DEBUG=False` 설정 확인
- [ ] `ALLOWED_HOSTS`에 실제 도메인 설정
- [ ] HTTPS 인증서 설치 및 설정

### 🗄️ 데이터베이스
- [ ] PostgreSQL 백업 전략 수립
- [ ] 초기 마이그레이션 실행
- [ ] 관리자 계정 생성
- [ ] 인덱스 생성 확인

### 🔧 서버 환경
- [ ] Docker & Docker Compose 최신 버전 설치
- [ ] 최소 4GB RAM, 20GB 저장 공간 확보
- [ ] 필요한 포트만 방화벽 오픈 (80, 443)
- [ ] 로그 로테이션 설정

## 📋 배포 단계별 체크리스트

### 1단계: 환경 준비
```bash
# 1. 환경 파일 생성
cp .env.example .env.prod

# 2. 환경 변수 설정 (중요!)
nano .env.prod
# 모든 기본값을 실제 운영 값으로 변경

# 3. 보안 검사
docker-compose exec backend python manage.py health_check --detailed
```

### 2단계: 컨테이너 빌드 및 시작
```bash
# 1. 프로덕션 환경으로 빌드
docker-compose -f docker-compose.prod.yml --env-file .env.prod build

# 2. 서비스 시작
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 3. 서비스 상태 확인
docker-compose ps
```

### 3단계: 초기 설정
```bash
# 1. 데이터베이스 마이그레이션
docker-compose exec backend python manage.py migrate

# 2. 정적 파일 수집
docker-compose exec backend python manage.py collectstatic --noinput

# 3. 관리자 계정 생성
docker-compose exec backend python manage.py createsuperuser
```

### 4단계: 최종 검증
```bash
# 1. 헬스체크 실행
curl https://yourdomain.com/api/health/detailed/

# 2. 주요 기능 테스트
# - 회원가입/로그인
# - 컨텐츠 생성
# - 리뷰 기능
# - AI 기능

# 3. 로그 확인
docker-compose logs -f
```

## 🚨 운영 후 모니터링

### 정기 점검 (매일)
- [ ] 서비스 상태: `curl /api/health/`
- [ ] 로그 확인: `docker-compose logs --tail=100`
- [ ] 디스크 사용량: `df -h`
- [ ] 메모리 사용량: `free -h`

### 정기 점검 (매주)
- [ ] 데이터베이스 백업 실행
- [ ] 보안 업데이트 확인
- [ ] 성능 지표 확인
- [ ] 에러 로그 분석

### 정기 점검 (매월)
- [ ] Docker 이미지 업데이트
- [ ] 의존성 패키지 업데이트 검토
- [ ] 백업 복구 테스트
- [ ] 보안 감사

## 🆘 트러블슈팅

### 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 개별 컨테이너 디버깅
docker-compose exec backend bash
docker-compose exec frontend sh
```

### 데이터베이스 연결 실패
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps db

# 데이터베이스 연결 테스트
docker-compose exec backend python manage.py dbshell
```

### Redis 연결 실패
```bash
# Redis 컨테이너 상태 확인
docker-compose ps redis

# Redis 연결 테스트
docker-compose exec backend python manage.py shell
# >>> from django.core.cache import cache
# >>> cache.set('test', 'ok')
```

## 📞 긴급 연락처
- **시스템 관리자**: [연락처 입력]
- **개발팀**: [연락처 입력]
- **인프라팀**: [연락처 입력]

## 🔗 유용한 링크
- **모니터링 대시보드**: https://yourdomain.com/admin/
- **API 문서**: https://yourdomain.com/api/docs/
- **헬스체크**: https://yourdomain.com/api/health/detailed/
- **백업 저장소**: [백업 위치]

---
**⚠️ 주의사항**: 이 체크리스트의 모든 항목을 완료한 후 운영 환경을 시작하세요.