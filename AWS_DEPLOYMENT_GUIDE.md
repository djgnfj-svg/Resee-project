# 🚀 Resee 프로젝트 AWS + Supabase 배포 가이드

AWS EC2 + Supabase PostgreSQL 아키텍처로 SSL까지 완전 배포하는 가이드입니다.
**현재 아키텍처**: EC2 (Docker) + Supabase (PostgreSQL) + CloudFlare (SSL)

## 📋 배포 전체 순서

```
1️⃣ AWS 계정 로그인 및 리전 설정
2️⃣ EC2 키 페어 생성
3️⃣ 보안 그룹 생성 및 설정
4️⃣ EC2 인스턴스 생성
5️⃣ 탄력적 IP 생성 및 연결
6️⃣ Route53 DNS 레코드 설정
7️⃣ EC2 서버 접속 및 기본 설정
8️⃣ 필수 라이브러리 설치
9️⃣ 프로젝트 배포
🔟 CloudFlare SSL 설정
1️⃣1️⃣ 최종 테스트 및 확인
```

---

## 🌍 **1단계: AWS 계정 로그인 및 기본 설정**

### **1-1. AWS Console 로그인**
1. **AWS Console** 접속: https://aws.amazon.com/console/
2. **"Sign In to the Console"** 클릭
3. 계정 정보 입력:
   - **Account ID (12 digits) 또는 account alias**
   - **IAM user name** (루트 계정인 경우 이메일)
   - **Password**
4. **"Sign in"** 클릭

### **1-2. 리전 선택**
1. 우상단 리전 선택 (현재 리전 표시)
2. **"Asia Pacific (Seoul) ap-northeast-2"** 선택
3. 모든 작업을 이 리전에서 수행

### **1-3. IAM 권한 확인**
배포에 필요한 최소 권한:
- EC2 인스턴스 생성/관리
- 보안 그룹 생성/수정
- 탄력적 IP 할당/연결
- Route53 레코드 수정

---

## 🔑 **2단계: EC2 키 페어 생성**

### **2-1. 키 페어 생성**
1. **EC2 대시보드** → 좌측 메뉴 **"네트워크 및 보안"** → **"키 페어"**
2. **"키 페어 생성"** 버튼 클릭
3. 키 페어 설정:
   ```
   이름: resee-keypair
   키 페어 유형: RSA
   프라이빗 키 파일 형식: .pem
   ```
4. **"키 페어 생성"** 클릭
5. **resee-keypair.pem** 파일 자동 다운로드

### **2-2. 키 파일 권한 설정 (Mac/Linux)**
```bash
# 다운로드 폴더로 이동
cd ~/Downloads

# 권한 설정 (필수!)
chmod 400 resee-keypair.pem

# 안전한 위치로 이동
mkdir -p ~/.ssh
mv resee-keypair.pem ~/.ssh/
```

### **2-3. Windows 사용자 권한 설정**
1. **resee-keypair.pem** 파일 우클릭 → **"속성"**
2. **"보안"** 탭 → **"고급"**
3. **"상속 사용 안함"** → **"이 개체에서 상속된 권한을 모두 제거"**
4. **"추가"** → **"보안 주체 선택"** → 현재 사용자만 추가
5. 권한: **"모든 권한"** 허용

---

## 🛡️ **3단계: 보안 그룹 생성**

### **3-1. 보안 그룹 생성**
1. **EC2 대시보드** → **"네트워크 및 보안"** → **"보안 그룹"**
2. **"보안 그룹 생성"** 클릭
3. 기본 정보 입력:
   ```
   보안 그룹 이름: resee-sg
   설명: Resee project security group
   VPC: 기본 VPC 선택
   ```

### **3-2. 인바운드 규칙 설정**
**"인바운드 규칙"** 섹션에서 다음 규칙 추가:

| 유형 | 포트 범위 | 소스 | 설명 |
|------|-----------|------|------|
| SSH | 22 | 0.0.0.0/0 | SSH 접속 |
| HTTP | 80 | 0.0.0.0/0 | 웹 서비스 |
| HTTPS | 443 | 0.0.0.0/0 | SSL 웹 서비스 |

각 규칙 추가 방법:
1. **"규칙 추가"** 클릭
2. **유형** 선택 (SSH, HTTP, HTTPS)
3. **소스**: "Anywhere-IPv4 (0.0.0.0/0)" 선택
4. **설명** 입력

### **3-3. 아웃바운드 규칙 확인**
- 기본값으로 모든 트래픽 허용 (수정 불필요)

**"보안 그룹 생성"** 클릭

---

## 🖥️ **4단계: EC2 인스턴스 생성**

### **4-1. 인스턴스 시작**
1. **EC2 대시보드** → **"인스턴스"** → **"인스턴스 시작"**

### **4-2. AMI 선택**
```
이름: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
아키텍처: 64비트 (x86)
```
**"선택"** 클릭

### **4-3. 인스턴스 유형 선택**
```
인스턴스 유형: t3.medium (2 vCPU, 4 GiB RAM)
```
> **중요**: t2.micro는 메모리 부족으로 빌드 실패 가능

### **4-4. 인스턴스 구성**
1. **인스턴스 개수**: 1
2. **네트워크**: 기본 VPC
3. **서브넷**: 기본값 (자동 할당)
4. **퍼블릭 IP 자동 할당**: 활성화

### **4-5. 스토리지 추가**
```
크기: 20 GiB (기본 8 GiB에서 최소 증가, 비용 최적화)
볼륨 유형: gp3 (범용 SSD)
삭제 시 종료: 체크
```

> **비용 참고**:
> - 8GB → 20GB: +$1.20/월 추가
> - 8GB → 30GB: +$2.20/월 추가

### **4-6. 태그 추가**
```
키: Name
값: resee-server
```

### **4-7. 보안 그룹 선택**
- **"기존 보안 그룹 선택"**
- **resee-sg** 선택

### **4-8. 키 페어 선택**
- **resee-keypair** 선택
- 약관 동의 체크

**"인스턴스 시작"** 클릭

### **4-9. 인스턴스 상태 확인**
- **"인스턴스 보기"** 클릭
- 상태가 **"running"**이 될 때까지 대기 (2-3분)

---

## 🌐 **5단계: 탄력적 IP 생성 및 연결**

### **5-1. 탄력적 IP 할당**
1. **EC2 대시보드** → **"네트워크 및 보안"** → **"탄력적 IP"**
2. **"탄력적 IP 주소 할당"** 클릭
3. 설정:
   ```
   네트워크 경계 그룹: ap-northeast-2a
   퍼블릭 IPv4 주소 풀: Amazon의 IPv4 주소 풀
   ```
4. **"할당"** 클릭

### **5-2. 탄력적 IP 연결**
1. 생성된 탄력적 IP 선택 (체크박스)
2. **"작업"** → **"탄력적 IP 주소 연결"**
3. 연결 설정:
   ```
   리소스 유형: 인스턴스
   인스턴스: resee-server 선택
   프라이빗 IP 주소: 자동 선택됨
   재연결 허용: 체크
   ```
4. **"연결"** 클릭

### **5-3. 연결 확인**
- 탄력적 IP 목록에서 **"연결된 인스턴스"** 컬럼에 resee-server 표시 확인

---

## 🌍 **6단계: Route53 DNS 설정**

### **6-1. 호스팅 영역 확인**
1. **Route53 대시보드** → **"호스팅 영역"**
2. **reseeall.com** 도메인 클릭 (이미 등록되어 있음)

### **6-2. A 레코드 생성 (루트 도메인)**
1. **"레코드 생성"** 클릭
2. 설정:
   ```
   레코드 이름: (비워둠) - 루트 도메인 @
   레코드 유형: A
   값: [탄력적_IP_주소] (예: 52.79.xxx.xxx)
   TTL: 300
   라우팅 정책: 단순 라우팅
   ```
3. **"레코드 생성"** 클릭

### **6-3. A 레코드 생성 (www 서브도메인)**
1. **"레코드 생성"** 클릭
2. 설정:
   ```
   레코드 이름: www
   레코드 유형: A
   값: [탄력적_IP_주소] (동일한 IP)
   TTL: 300
   ```
3. **"레코드 생성"** 클릭

### **6-4. DNS 전파 확인**
```bash
# 로컬 터미널에서 확인 (5-10분 소요)
nslookup reseeall.com
nslookup www.reseeall.com

# 정상적이면 탄력적 IP가 응답으로 나타남
```

---

## 🔗 **7단계: EC2 서버 접속 및 기본 설정**

### **7-1. SSH 접속**
```bash
# Mac/Linux 터미널
ssh -i ~/.ssh/resee-keypair.pem ubuntu@reseeall.com

# 처음 접속 시 fingerprint 확인 메시지에서 'yes' 입력
```

**Windows 사용자 (PuTTY 사용)**:
1. PuTTY 다운로드 및 설치
2. PuTTYgen으로 .pem을 .ppk로 변환
3. PuTTY에서 Host Name: ubuntu@reseeall.com, Port: 22
4. Connection → SSH → Auth → Private key file에서 .ppk 파일 선택

### **7-2. 서버 정보 확인**
```bash
# 시스템 정보 확인
uname -a
lsb_release -a

# 디스크 용량 확인
df -h

# 메모리 확인
free -h
```

### **7-3. 시스템 업데이트**
```bash
# 패키지 목록 업데이트
sudo apt update

# 패키지 업그레이드
sudo apt upgrade -y

# 재부팅 필요 시
sudo reboot
# 재부팅 후 다시 SSH 접속
```

---

## 📦 **8단계: 필수 라이브러리 설치**

### **8-1. 기본 개발 도구 설치**
```bash
# 필수 패키지만 설치 (용량 최적화)
sudo apt update
sudo apt install -y \
    curl \
    git \
    ca-certificates

# 설치 확인
git --version
curl --version
```

> **최적화**: 불필요한 패키지 제거로 수백 MB 디스크 공간 절약

### **8-2. 방화벽 설정**
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 방화벽 활성화
sudo ufw enable

# 상태 확인
sudo ufw status
```

### **8-3. 타임존 설정**
```bash
# 한국 표준시 설정
sudo timedatectl set-timezone Asia/Seoul

# 확인
timedatectl
```

---

## 🚀 **9단계: 프로젝트 배포**

### **9-1. 프로젝트 클론**
```bash
# 홈 디렉토리에서 실행
cd ~

# GitHub에서 프로젝트 클론
git clone https://github.com/djgnfj-svg/Resee-project.git

# 프로젝트 디렉토리로 이동
cd Resee-project

# 파일 목록 확인
ls -la
```

### **9-2. 환경 변수 파일 생성**
```bash
# .env.prod 파일 복사
cp .env.example .env.prod

# 환경 변수 편집
nano .env.prod
```

**중요 환경 변수 설정** (Supabase 아키텍처):
```bash
# Django 설정
SECRET_KEY=your-very-secure-secret-key-here
DJANGO_SETTINGS_MODULE=resee.settings.production
ALLOWED_HOSTS=reseeall.com,www.reseeall.com
CSRF_TRUSTED_ORIGINS=https://reseeall.com,https://www.reseeall.com

# Supabase 데이터베이스 설정 (기존 PostgreSQL 설정 대체)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.zmioqzfmnkhkzgpkadfm.supabase.co:5432/postgres
SUPABASE_URL=https://zmioqzfmnkhkzgpkadfm.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# 이메일 설정
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
ENFORCE_EMAIL_VERIFICATION=True

# 프론트엔드 URL
FRONTEND_URL=https://reseeall.com
REACT_APP_API_URL=https://reseeall.com/api

```

> **중요**: 실제 Supabase 프로젝트 URL과 키로 교체 필요

저장: `Ctrl + X` → `Y` → `Enter`

### **9-3. 배포 스크립트 실행**
```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행 (Docker 자동 설치 포함)
./deploy.sh
```

배포 스크립트가 자동으로 처리하는 내용:
- Docker & Docker Compose 설치
- 환경 변수 검증
- Swap 메모리 추가 (메모리 부족 시)
- Docker 이미지 빌드
- 컨테이너 시작
- 데이터베이스 연결 및 마이그레이션 적용
- 정적 파일 수집

### **9-4. 배포 상태 확인**
```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 웹 사이트 접속 테스트
curl -I http://reseeall.com
```

---

## 🌟 **10단계: CloudFlare SSL 설정**

### **10-1. CloudFlare 계정 생성**
1. https://cloudflare.com 접속
2. **"Sign Up"** 클릭
3. 이메일과 비밀번호 입력
4. 이메일 인증 완료

### **10-2. 도메인 추가**
1. 로그인 후 **"Add a Site"** 클릭
2. 도메인 입력: `reseeall.com`
3. **"Add Site"** 클릭
4. 플랜 선택: **"Free $0/month"** 선택 → **"Continue"**

### **10-3. DNS 레코드 확인**
CloudFlare가 기존 DNS를 스캔한 후 다음 레코드 확인:

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| A | @ | [EC2_IP] | ☁️ Proxied |
| A | www | [EC2_IP] | ☁️ Proxied |

> **중요**: Proxy Status가 반드시 **"Proxied"** (주황색 구름)여야 함

### **10-4. SSL/TLS 설정**
1. **"SSL/TLS"** 탭 클릭
2. **"Overview"** → **Encryption mode**: **"Full (strict)"** 선택
3. **"Edge Certificates"** 섹션:
   ```
   ✅ Always Use HTTPS: ON
   ✅ HTTP Strict Transport Security (HSTS): Enable
   ✅ Minimum TLS Version: 1.2
   ✅ TLS 1.3: ON
   ✅ Automatic HTTPS Rewrites: ON
   ```

### **10-5. 페이지 규칙 설정**
1. **"Rules"** → **"Page Rules"** 클릭
2. **"Create Page Rule"** 클릭
3. 설정:
   ```
   URL: http://*reseeall.com/*
   Setting: Always Use HTTPS
   ```
4. **"Save and Deploy"** 클릭

### **10-6. 네임서버 변경**
**AWS Route53에서 네임서버 변경**:
1. **Route53 Console** → **"Registered domains"** → **"reseeall.com"**
2. **"Add or edit name servers"** 클릭
3. 기존 네임서버 삭제 후 CloudFlare 네임서버 입력:
   ```
   예시 (CloudFlare에서 제공되는 실제 값 사용):
   ava.ns.cloudflare.com
   bob.ns.cloudflare.com
   ```
4. **"Update"** 클릭

### **10-7. DNS 전파 대기**
```bash
# DNS 전파 확인 (5분-24시간 소요)
nslookup reseeall.com 8.8.8.8
nslookup reseeall.com 1.1.1.1

# CloudFlare가 활성화되면 CloudFlare IP 표시
# 예: 104.21.x.x 또는 172.67.x.x
```

---

## ⚙️ **11단계: 애플리케이션 HTTPS 설정**

### **11-1. Django HTTPS 설정 확인**
```bash
# EC2에서 실행
cd ~/Resee-project

# 프로덕션 설정 확인
cat backend/resee/settings/production.py | grep -E "(SECURE_|USE_)"
```

다음 설정이 이미 포함되어 있어야 함:
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_CF_VISITOR', '{"scheme":"https"}')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
```

### **11-2. 환경 변수 HTTPS 업데이트**
```bash
# .env.prod 파일 수정
nano .env.prod

# 다음 라인 수정
FRONTEND_URL=https://reseeall.com
CSRF_TRUSTED_ORIGINS=https://reseeall.com,https://www.reseeall.com
ALLOWED_HOSTS=reseeall.com,www.reseeall.com
```

### **11-3. 컨테이너 재시작**
```bash
# 환경 변수 적용을 위한 재시작
docker-compose -f docker-compose.prod.yml restart

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### **11-4. Google OAuth HTTPS 설정**
**Google Cloud Console에서**:
1. Google Cloud Console → 프로젝트 선택
2. **"API 및 서비스"** → **"사용자 인증 정보"**
3. OAuth 클라이언트 ID 편집
4. **"승인된 JavaScript 원본"** 업데이트:
   ```
   https://reseeall.com
   https://www.reseeall.com
   ```
5. HTTP 원본은 삭제

---

## ✅ **12단계: 최종 테스트 및 확인**

### **12-1. HTTPS 접속 테스트**
```bash
# SSL 인증서 확인
curl -I https://reseeall.com

# 응답 헤더에서 다음 확인:
# - HTTP/2 200
# - server: cloudflare
# - 기타 보안 헤더들
```

### **12-2. 브라우저 테스트**
1. https://reseeall.com 접속
2. 주소창 🔒 아이콘 확인
3. 인증서 클릭 → CloudFlare 발급 확인
4. HTTP → HTTPS 자동 리다이렉트 확인

### **12-3. 애플리케이션 기능 테스트**
- [ ] 회원가입 테스트
- [ ] 이메일 인증 테스트
- [ ] 로그인 테스트
- [ ] Google OAuth 테스트
- [ ] 콘텐츠 생성 테스트
- [ ] 리뷰 시스템 테스트

### **12-4. 성능 테스트**
```bash
# SSL 등급 확인
# https://www.ssllabs.com/ssltest/ 에서 도메인 테스트
# 목표: A+ 등급

# 페이지 로딩 속도 확인
curl -w "@curl-format.txt" -o /dev/null -s https://reseeall.com

# curl-format.txt 파일 생성
echo "     time_namelookup:  %{time_namelookup}\\n
        time_connect:  %{time_connect}\\n
     time_appconnect:  %{time_appconnect}\\n
    time_pretransfer:  %{time_pretransfer}\\n
       time_redirect:  %{time_redirect}\\n
  time_starttransfer:  %{time_starttransfer}\\n
                     ----------\\n
          time_total:  %{time_total}\\n" > curl-format.txt
```

---

## 🔧 **문제 해결 가이드**

### **EC2 접속 문제**
```bash
# 권한 에러
chmod 400 ~/.ssh/resee-keypair.pem

# 연결 거부
# 1. 보안 그룹에서 포트 22 확인
# 2. 인스턴스 상태 확인 (running)
# 3. 탄력적 IP 연결 확인

# 타임아웃
# 1. 올바른 퍼블릭 IP 사용 확인
# 2. 네트워크 연결 확인
```

### **Docker 메모리 부족**
```bash
# Swap 추가 (deploy.sh가 자동 처리하지만 수동으로도 가능)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### **SSL 인증서 문제**
```bash
# DNS 전파 상태 확인
dig reseeall.com @8.8.8.8
dig reseeall.com @1.1.1.1

# CloudFlare 상태 확인
# CloudFlare Dashboard에서 도메인 상태가 "Active" (초록색)인지 확인

# 캐시 지우기
# 브라우저 캐시 및 CloudFlare 캐시 퍼지
```

### **컨테이너 재시작**
```bash
# 모든 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart

# 특정 컨테이너만 재시작
docker-compose -f docker-compose.prod.yml restart backend

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f backend
```

### **데이터베이스 연결 문제**
```bash
# 환경 변수 확인
docker-compose -f docker-compose.prod.yml exec backend env | grep -E "(DATABASE_URL|SUPABASE)"

# 데이터베이스 연결 테스트
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell --command="\q"

# Django 연결 테스트
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell -c "from django.db import connection; connection.cursor()"

# 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart backend
```

---

## 📊 **비용 예상** (t3.small 최적화)

| 서비스 | 월 예상 비용 | 설명 |
|--------|-------------|------|
| EC2 t3.small | $15-20 | 24시간 운영 |
| 탄력적 IP | $3.60 | 연결된 상태 |
| EBS 스토리지 20GB | $2 | gp3 볼륨 (최적화) |
| Route53 호스팅 | $0.50 | 호스팅 영역 |
| Supabase Pro | $25 | PostgreSQL 호스팅 |
| CloudFlare SSL | $0 | 무료 플랜 |
| **총합** | **$46-51** | **월 예상 비용** |

**스토리지 옵션별 비용:**
- 20GB (권장): $2/월
- 30GB: $3/월 (+$1 추가)

---

## 📝 **중요 명령어 모음**

```bash
# 서버 접속
ssh -i ~/.ssh/resee-keypair.pem ubuntu@reseeall.com

# 프로젝트 디렉토리
cd ~/Resee-project

# 컨테이너 관리
docker-compose -f docker-compose.prod.yml ps        # 상태 확인
docker-compose -f docker-compose.prod.yml logs -f   # 로그 확인
docker-compose -f docker-compose.prod.yml restart   # 재시작
docker-compose -f docker-compose.prod.yml down      # 중지
docker-compose -f docker-compose.prod.yml up -d     # 시작

# 백업 생성
sudo tar -czf ~/resee-backup-$(date +%Y%m%d).tar.gz \
    ~/Resee-project \
    ~/.ssh/resee-keypair.pem

# 시스템 모니터링
htop                    # 리소스 사용량
df -h                   # 디스크 사용량
free -h                 # 메모리 사용량
docker stats            # 컨테이너 리소스 사용량
```

---

## 🎯 **최종 체크리스트**

```
✅ AWS 계정 로그인 및 서울 리전 설정
✅ EC2 키 페어 생성 및 권한 설정
✅ 보안 그룹 생성 (SSH, HTTP, HTTPS)
✅ EC2 인스턴스 생성 (t3.medium, Ubuntu 22.04)
✅ 탄력적 IP 할당 및 연결
✅ Route53 A 레코드 설정 (@ 및 www)
✅ EC2 SSH 접속 및 시스템 업데이트
✅ 필수 패키지 설치 및 방화벽 설정
✅ 프로젝트 클론 및 환경 변수 설정
✅ deploy.sh 실행으로 Docker 설치 및 배포
✅ HTTP 접속 테스트
✅ CloudFlare 계정 생성 및 도메인 추가
✅ CloudFlare SSL/TLS 설정
✅ Route53 네임서버 → CloudFlare 변경
✅ DNS 전파 대기 및 HTTPS 설정
✅ 모든 기능 테스트 완료
✅ SSL A+ 등급 확인
```

이제 **https://reseeall.com**으로 완전한 SSL 보안이 적용된 Resee 서비스에 접속할 수 있습니다! 🎉