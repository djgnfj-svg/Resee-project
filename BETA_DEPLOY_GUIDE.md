# 🚀 Resee Beta 배포 가이드

간단한 베타 배포를 위한 단계별 가이드입니다.

## 📋 배포 개요

**구성**: AWS RDS PostgreSQL + Docker Compose (서버)
**특징**: DB만 클라우드, 나머지는 단일 서버
**비용**: 월 $15-30 (RDS + 서버)

---

## 1️⃣ AWS RDS 설정 (5분)

### RDS PostgreSQL 생성
1. AWS 콘솔 → RDS → "Create database"
2. 설정:
   ```
   Engine: PostgreSQL 15
   Templates: Free tier
   DB instance identifier: resee-beta-db
   Master username: resee_admin
   Master password: [강력한 비밀번호]
   DB instance class: db.t3.micro
   Storage: 20 GB
   ```
3. **중요**: "Public access" → **Yes** 선택
4. Security Group → Inbound rules:
   ```
   Type: PostgreSQL
   Port: 5432
   Source: Anywhere (0.0.0.0/0)  # 베타용만!
   ```

### 엔드포인트 확인
- RDS 콘솔에서 생성된 DB의 "Endpoint" 복사
- 예: `resee-beta-db.xxxx.us-east-1.rds.amazonaws.com`

---

## 2️⃣ 서버 준비 (3분)

### EC2 인스턴스 (또는 다른 서버)
```bash
# Ubuntu 20.04+ 기준
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 프로젝트 클론
git clone [저장소]
cd Resee
```

---

## 3️⃣ 환경변수 설정 (2분)

```bash
# .env.beta 파일 생성
cp .env.beta.example .env.beta
nano .env.beta
```

### 필수 수정 항목:
```env
# 보안키 (50자 이상)
SECRET_KEY=매우-강력한-시크릿-키-50자-이상

# 도메인 (서버 IP 또는 도메인)
ALLOWED_HOSTS=your-server-ip,your-domain.com
CORS_ALLOWED_ORIGINS=http://your-domain.com
REACT_APP_API_URL=http://your-domain.com/api

# RDS 연결 (위에서 생성한 정보)
DATABASE_URL=postgresql://resee_admin:패스워드@resee-beta-db.xxxx.us-east-1.rds.amazonaws.com:5432/postgres

# AI API (필수)
ANTHROPIC_API_KEY=your-anthropic-key

# OAuth (선택사항)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret

# Stripe (테스트 키)
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
```

---

## 4️⃣ 배포 실행 (5분)

```bash
# 배포 스크립트 실행
./deploy-beta.sh
```

**스크립트가 자동으로 처리:**
- 환경변수 검증
- DB 연결 테스트  
- Docker 이미지 빌드
- 컨테이너 시작
- 헬스체크

---

## 5️⃣ 관리자 계정 생성 (1분)

```bash
# 슈퍼유저 생성
docker-compose -f docker-compose.beta.yml exec backend python manage.py createsuperuser
```

---

## 🎉 완료!

**접속 URL:**
- 웹사이트: `http://your-domain.com`
- 관리자: `http://your-domain.com/admin/`
- API: `http://your-domain.com/api/`

---

## 📊 모니터링 명령어

```bash
# 상태 확인
docker-compose -f docker-compose.beta.yml ps

# 로그 확인
docker-compose -f docker-compose.beta.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.beta.yml logs backend
docker-compose -f docker-compose.beta.yml logs frontend

# 컨테이너 재시작
docker-compose -f docker-compose.beta.yml restart backend

# 전체 중단
docker-compose -f docker-compose.beta.yml down
```

---

## 🔧 문제 해결

### DB 연결 오류
```bash
# RDS 보안그룹 확인
# PostgreSQL(5432) 포트가 열려있는지 확인

# 연결 테스트
psql "postgresql://username:password@endpoint:5432/postgres"
```

### 컨테이너 실행 오류
```bash
# 로그 확인
docker-compose -f docker-compose.beta.yml logs backend

# 환경변수 확인
docker-compose -f docker-compose.beta.yml exec backend env | grep DATABASE_URL
```

### 도메인 연결
```bash
# DNS 설정
A 레코드: your-domain.com → server-ip

# NGINX 설정 확인
docker-compose -f docker-compose.beta.yml exec nginx nginx -t
```

---

## 💰 예상 비용

- **RDS db.t3.micro**: ~$13/월
- **EC2 t3.small**: ~$15/월
- **총 비용**: ~$30/월

---

## 🚀 다음 단계 (운영 준비시)

1. **SSL 인증서**: Let's Encrypt 또는 CloudFlare
2. **도메인**: Route 53 또는 CloudFlare  
3. **백업**: RDS 자동 백업 활성화
4. **모니터링**: CloudWatch 또는 Datadog
5. **스케일링**: Load Balancer + Auto Scaling

---

**🎯 이 설정으로 베타 서비스 시작 완료!**