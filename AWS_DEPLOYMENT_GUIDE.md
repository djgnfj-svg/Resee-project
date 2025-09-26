# 🚀 Resee AWS EC2 + Supabase 배포 가이드

**최신 아키텍처**: EC2 (Docker) + Supabase (PostgreSQL) + IPv6 지원

## 📋 1단계: EC2 인스턴스 생성 (IPv6 설정 포함)

### 1️⃣ AWS VPC IPv6 설정
1. **VPC 콘솔** → 기존 VPC 선택 → **"Actions"** → **"Edit CIDRs"**
2. **"Add IPv6 CIDR"** → **"Amazon 제공 IPv6 CIDR 블록"** 선택 → **"CIDR 선택"**

### 2️⃣ 서브넷 IPv6 설정
1. **VPC** → **서브넷** → EC2용 서브넷 선택
2. **"Actions"** → **"IPv6 CIDR 편집"** → **"IPv6 CIDR 추가"**
3. 자동 할당된 IPv6 CIDR 선택 (예: `2406:da12:xxx::/64`)

### 3️⃣ EC2 인스턴스 생성
**EC2 콘솔 → Launch Instance:**

**기본 설정:**
```
AMI: Ubuntu 22.04 LTS
Instance Type: t3.small (권장)
Key Pair: 새로 생성 또는 기존 사용
```

**네트워크 설정 (중요!):**
```
VPC: IPv6가 설정된 VPC 선택
서브넷: IPv6가 설정된 서브넷 선택
Auto-assign public IP: ✅ Enable
Auto-assign IPv6 IP: ✅ Enable (핵심!)
```

**보안 그룹:**
```
SSH (22): 0.0.0.0/0, ::/0
HTTP (80): 0.0.0.0/0, ::/0
HTTPS (443): 0.0.0.0/0, ::/0
Custom TCP (8000): 0.0.0.0/0, ::/0
All traffic (Outbound): 0.0.0.0/0, ::/0
```

**스토리지:** 20GB gp3

---

## 📦 2단계: EC2 서버 설정

### 1️⃣ SSH 접속
```bash
# 키 파일 권한 설정
chmod 400 ~/.ssh/your-keypair.pem

# EC2 접속
ssh -i ~/.ssh/your-keypair.pem ubuntu@https://reseeall.com
```

### 2️⃣ IPv6 연결 확인
```bash
# IPv6 주소 확인 (글로벌 IPv6 주소가 있어야 함)
ip -6 addr show

# Supabase 연결 테스트
ping6 -c 3 db.zmioqzfmnkhkzgpkadfm.supabase.co
ping -c 3 db.zmioqzfmnkhkzgpkadfm.supabase.co
```

> **중요**: IPv6 주소가 `2xxx:xxx:xxx` 형태로 나와야 합니다. `fe80::` 는 로컬 주소입니다.

### 3️⃣ 시스템 기본 설정
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y curl git

# 프로젝트 클론
cd ~
git clone https://github.com/djgnfj-svg/Resee-project.git
cd Resee-project
```

---

## 🔧 3단계: 환경 변수 설정

### 1️⃣ .env.prod 파일 생성
```bash
# 환경 변수 파일 복사
cp .env.example .env.prod

# 환경 변수 편집
vim .env.prod
```

---

## 🚀 4단계: 애플리케이션 배포

### 1️⃣ 배포 스크립트 실행
```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행 (Docker 자동 설치 포함)
./deploy.sh
newgrp docker
./deploy.sh

```

> **배포 과정** (5-10분 소요):
> - Docker & Docker Compose 자동 설치
> - 환경 변수 검증
> - Swap 메모리 추가 (필요시)
> - Docker 이미지 빌드
> - 컨테이너 시작 및 헬스체크
> - 데이터베이스 마이그레이션
> - 정적 파일 수집

### 2️⃣ 배포 상태 확인
```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 모든 컨테이너가 "Up" 상태여야 함:
# - backend (healthy)
# - frontend (healthy)
# - nginx
```

### 3️⃣ 웹사이트 접속 테스트
```bash
# API 헬스체크
curl -I http://https://reseeall.com/api/health/

# 메인 페이지 확인
curl -I http://https://reseeall.com
```

---

## 🔧 문제 해결

### Supabase 연결 실패
```bash
# IPv6 연결 확인
ping6 db.zmioqzfmnkhkzgpkadfm.supabase.co

docker-compose -f docker-compose.prod.yml restart backend
```

### 컨테이너 시작 실패
```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs backend --tail=20
docker-compose -f docker-compose.prod.yml logs frontend --tail=20

# 개별 서비스 재시작
docker-compose -f docker-compose.prod.yml restart backend
```

---

## 📊 주요 명령어 모음

```bash
# 서버 접속
ssh -i ~/.ssh/your-keypair.pem ubuntu@https://reseeall.com

# 프로젝트 디렉토리
cd ~/Resee-project

# 컨테이너 관리
docker-compose -f docker-compose.prod.yml ps        # 상태
docker-compose -f docker-compose.prod.yml logs -f   # 로그
docker-compose -f docker-compose.prod.yml restart   # 재시작
docker-compose -f docker-compose.prod.yml down      # 중지
docker-compose -f docker-compose.prod.yml up -d     # 시작

# 시스템 모니터링
free -h                 # 메모리 사용량
df -h                   # 디스크 사용량
docker stats            # 컨테이너 리소스
```

---

## ✅ 배포 완료 체크리스트

```
✅ AWS EC2 인스턴스 생성 (IPv6 포함)
✅ SSH 접속 확인
✅ IPv6 글로벌 주소 할당 확인
✅ Supabase 연결 테스트 성공
✅ 프로젝트 클론 완료
✅ .env.prod 환경 변수 설정
✅ deploy.sh 실행 성공
✅ 모든 컨테이너 정상 실행
✅ 웹사이트 접속 확인 (http://https://reseeall.com)
✅ 회원가입/로그인 기능 테스트
✅ 콘텐츠 생성/리뷰 시스템 테스트
```