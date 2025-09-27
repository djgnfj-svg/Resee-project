# Resee v0.1

과학적 스페이스드 리페티션 학습 플랫폼

## 핵심 기능

- **과학적 복습 시스템**: Ebbinghaus 망각곡선 기반 알고리즘
- **AI 주간 시험**: 자동 문제 생성 및 평가
- **구독 시스템**: FREE/BASIC/PRO 티어별 기능 제한
- **반응형 웹**: 모바일/데스크톱 최적화

## 빠른 시작

### 개발 환경
```bash
# 환경 설정
cp .env.example .env

# 서비스 시작
docker-compose up -d

# 마이그레이션
docker-compose exec backend python manage.py migrate

# 접속
http://localhost  # Nginx 통합 접속
```

### 프로덕션 배포
```bash
# 프로덕션 환경 설정
cp .env.prod.example .env.prod

# 배포
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## 기술 스택

**Backend**: Django + PostgreSQL + Anthropic API
**Frontend**: React + TypeScript + TailwindCSS
**Infrastructure**: Docker + Nginx

## 환경 변수

```bash
# 필수
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...

# 선택 (AI 기능용)
ANTHROPIC_API_KEY=sk-ant-api...
```