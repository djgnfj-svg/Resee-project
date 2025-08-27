# 🚀 Resee v0.1.0 

에빙하우스 망각곡선 기반 AI 학습 복습 플랫폼

## 🎯 핵심 기능

- **🧠 과학적 복습 시스템**: 에빙하우스 망각곡선 알고리즘
- **🤖 AI 문제 생성**: Claude API 기반 자동 문제 생성
- **📊 학습 분석**: 실시간 학습 패턴 분석  
- **💰 구독 시스템**: FREE/BASIC/PRO 3단계
- **📱 반응형 웹**: React + TypeScript

## ⚡ 빠른 시작

### 1. 환경 설정
```bash
# 환경변수 설정
cp .env.example .env
vim .env  # SECRET_KEY, ANTHROPIC_API_KEY 입력
```

### 2. 배포 실행
```bash
# EC2 배포
./deploy-ec2.sh
```

### 3. 접속
- 웹사이트: http://your-server-ip:3000
- 관리자: http://your-server-ip:8000/admin

## 🏗️ 기술 스택

**Backend**
- Django 4.2 + DRF
- PostgreSQL + Redis  
- Celery + RabbitMQ
- Claude API

**Frontend**
- React 18 + TypeScript
- TailwindCSS + TipTap
- React Query

## 📋 필수 요구사항

- Docker & Docker Compose
- Anthropic API Key ([가입](https://console.anthropic.com/))
- 최소 2GB RAM 서버

## 🔧 유용한 명령어

```bash
# 로그 확인
docker-compose logs -f

# 서비스 재시작
docker-compose restart

# 데이터베이스 마이그레이션
docker-compose exec backend python manage.py migrate

# 관리자 계정 생성
docker-compose exec backend python manage.py createsuperuser
```

## 📊 구독 플랜

| 플랜 | 복습 간격 | AI 문제/일 | 가격 |
|------|----------|-----------|------|
| FREE | 1-3일 | 0개 | 무료 |
| BASIC | 1-90일 | 30개 | $9.99 |
| PRO | 1-180일 | 200개 | $19.99 |

## 🚀 v0.1.0 출시 준비 완료 ✅