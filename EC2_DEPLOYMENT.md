# EC2 배포 가이드

## EC2에서 HTTP-only 배포하기

### 1. EC2 인스턴스 준비
```bash
# Docker 설치
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

### 2. 프로젝트 클론 및 설정
```bash
# 프로젝트 클론
git clone https://github.com/yourusername/resee.git
cd resee

# .env 파일 생성 (EC2 IP로 수정)
cp .env.example .env
```

### 3. .env 파일 수정
```bash
# EC2 인스턴스 시작 후 퍼블릭 IP 확인
curl http://169.254.169.254/latest/meta-data/public-ipv4

# .env 파일에서 IP 주소 수정
REACT_APP_API_URL=http://YOUR_EC2_PUBLIC_IP:8000/api
ALLOWED_HOSTS=*
CORS_ALLOW_ALL_ORIGINS=True
DEBUG=True
```

**중요:** EC2는 도메인을 제공하지 않습니다. 퍼블릭 IP 주소만 제공됩니다.
- 예시: `http://54.123.45.67:3000`

### 4. 보안 그룹 설정
AWS 콘솔에서 다음 포트를 열어주세요:
- **포트 8000**: Django 백엔드 API
- **포트 3000**: React 프론트엔드
- **포트 22**: SSH 접속

### 5. 배포 실행
```bash
# 컨테이너 시작
docker-compose up -d --build

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### 6. 접속 확인
- **프론트엔드**: `http://YOUR_EC2_PUBLIC_IP:3000`
- **백엔드 API**: `http://YOUR_EC2_PUBLIC_IP:8000/api`
- **Django Admin**: `http://YOUR_EC2_PUBLIC_IP:8000/admin`

### 7. 테스트 계정
자동 생성된 테스트 계정으로 바로 테스트 가능:
- **admin@resee.com** / **admin123!**
- **test@resee.com** / **test123!**
- **demo@resee.com** / **demo123!**

### 주의사항
- 현재 설정은 테스트/개발용입니다
- 프로덕션 환경에서는 SSL 인증서 설정 필요
- 데이터베이스 백업 정책 수립 권장