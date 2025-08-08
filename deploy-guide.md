# 🚀 Resee 배포 가이드

## 옵션 1: Vercel + Supabase (추천 - 완전 무료)

### 필요한 것
- GitHub 계정
- Vercel 계정 (GitHub으로 가입)
- Supabase 계정 (GitHub으로 가입)

### 1단계: GitHub에 코드 푸시
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2단계: Supabase 설정 (백엔드 + DB)
1. https://supabase.com 접속
2. New Project 생성
3. Database 비밀번호 설정 (잘 기억해두세요!)
4. 프로젝트 생성 완료 후:
   - Settings → API → URL 복사 (SUPABASE_URL)
   - Settings → API → anon key 복사 (SUPABASE_ANON_KEY)

### 3단계: Django 백엔드를 Supabase Edge Function으로 변환
```javascript
// supabase/functions/api/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  // Django API 로직을 여기로 이전
  const { url, method } = req
  
  // 라우팅 처리
  if (url.includes('/api/auth/')) {
    // 인증 처리
  } else if (url.includes('/api/content/')) {
    // 콘텐츠 처리
  }
  
  return new Response(JSON.stringify({ message: "OK" }), {
    headers: { "Content-Type": "application/json" },
  })
})
```

### 4단계: Vercel에 프론트엔드 배포
1. https://vercel.com 접속
2. Import Git Repository
3. 환경 변수 설정:
   ```
   REACT_APP_API_URL=https://your-project.supabase.co/functions/v1
   REACT_APP_SUPABASE_URL=your-supabase-url
   REACT_APP_SUPABASE_ANON_KEY=your-anon-key
   ```
4. Deploy 클릭!

---

## 옵션 2: Railway (월 $5, 가장 간단)

### 1단계: Railway 설정
1. https://railway.app 가입
2. New Project → Deploy from GitHub repo
3. 환경 변수 자동 감지됨

### 2단계: 서비스 추가
Railway에서 + 버튼으로 추가:
- PostgreSQL
- Redis  
- RabbitMQ (필요시)

### 3단계: 배포
```bash
# railway.json 생성
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

자동으로 배포됨!

---

## 옵션 3: Oracle Cloud (완전 무료, 평생)

### 1단계: Oracle Cloud 가입
1. https://cloud.oracle.com 가입 (신용카드 필요하지만 과금 안됨)
2. Always Free 리소스 선택

### 2단계: VM 인스턴스 생성
```bash
# 2개 VM 생성 (각 1GB RAM)
# VM1: Frontend + Nginx
# VM2: Backend + DB + Redis
```

### 3단계: Docker 설치 및 배포
```bash
# SSH로 접속
ssh ubuntu@your-vm-ip

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 코드 클론
git clone https://github.com/your-username/resee.git
cd resee

# 환경 변수 설정
cp .env.example .env
nano .env  # 실제 값 입력

# 실행
docker-compose up -d
```

### 4단계: 포트 열기
Oracle Cloud Console에서:
1. Networking → Virtual Cloud Networks
2. Security List → Ingress Rules
3. Add: 80, 443 포트 열기

---

## 🔧 프로덕션 최적화

### Frontend 빌드 최적화
```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Backend 최적화
```python
# settings_prod.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# Static files
STATIC_ROOT = '/app/staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
```

### Docker Compose 프로덕션
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: resee-backend:latest
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

---

## 🎯 추천 배포 전략

### 초기 (무료)
1. **Vercel** (Frontend) + **Supabase** (Backend/DB)
2. 또는 **Railway** 무료 크레딧 사용

### 성장기 (월 $5-20)
1. **Railway** 또는 **Render** 유료 플랜
2. **DigitalOcean App Platform**

### 안정기 (월 $20+)
1. **AWS Lightsail** 또는 **DigitalOcean Droplet**
2. **Google Cloud Run** (자동 스케일링)

---

## 📝 배포 체크리스트

- [ ] 환경 변수 설정 (.env)
- [ ] DEBUG=False 설정
- [ ] ALLOWED_HOSTS 설정
- [ ] Static files 설정
- [ ] Database 마이그레이션
- [ ] SSL 인증서 설정
- [ ] 도메인 연결
- [ ] 모니터링 설정
- [ ] 백업 설정

---

## 🆘 문제 해결

### 메모리 부족
- Celery worker 수 줄이기
- gunicorn worker 수 줄이기
- Docker 메모리 제한 설정

### 느린 응답
- Database 인덱스 추가
- Redis 캐싱 활용
- CDN 사용 (Cloudflare)

### 비용 절감
- 이미지 최적화 (WebP 변환)
- Static files → CDN
- Database 쿼리 최적화