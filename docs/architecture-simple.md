# Resee 아키텍처 구성 설명

## 1단계: 외부 접근 계층

### 사용자 → Cloudflare SSL/TLS
```
사용자(브라우저) --HTTPS--> Cloudflare
```

**Cloudflare 역할**:
- **SSL/TLS 암호화**: HTTP를 HTTPS로 보호
- **DDoS 방어**: 악의적인 트래픽 차단
- **CDN**: 정적 파일 캐싱으로 속도 향상
- **무료**: 비용 없이 프로덕션급 보안

**왜 Cloudflare?**
- AWS ALB/CloudFront 대신 무료 대안
- 자동 SSL 인증서 발급 및 갱신
- DNS 관리 포함

---

## 2단계: AWS 인프라 계층

### Cloudflare → EC2
```
Cloudflare --HTTPS--> EC2 인스턴스
                       ↓
                     VPC (격리된 네트워크)
                       ↓
                    S3 (백업 저장소)
```

**AWS VPC (Virtual Private Cloud)**:
- **격리된 네트워크**: 외부에서 직접 접근 불가
- **Security Groups**: 방화벽 규칙 (포트 80, 443만 허용)
- **프라이빗 IP**: 내부 통신용

**EC2 인스턴스**:
- **역할**: Docker Compose 실행 환경
- **타입**: t3.medium (2 vCPU, 4GB RAM)
- **OS**: Ubuntu 22.04

**S3 버킷**:
- **용도**: PostgreSQL 백업 저장
- **백업 주기**: 매일 새벽 3시 (Celery Beat)
- **보관 기간**: 30일 (자동 삭제)

**GitHub Actions**:
- **배포 방식**: SSH로 EC2 접속 → deploy.sh 실행
- **자동화**: 코드 푸시 시 자동 배포
- **알림**: Slack으로 배포 성공/실패 통보

---

## 3단계: 애플리케이션 계층 (Docker Compose)

### EC2 → Nginx → Application
```
EC2 내부:
├── Nginx (웹서버)
│   ├── /api/* → Django
│   └── / → React
│
├── Application (비즈니스 로직)
│   ├── Django API (REST API 서버)
│   ├── React Frontend (사용자 UI)
│   └── Celery Worker (백그라운드 작업)
│
└── Data Layer (데이터 저장)
    ├── PostgreSQL (메인 DB)
    └── Redis (캐시 & 메시지 큐)
```

**Nginx 웹서버**:
- **리버스 프록시**: 외부 요청을 Django/React로 전달
- **경로 라우팅**:
  - `/api/*` → Django (8000번 포트)
  - `/` → React (정적 파일)
- **Rate Limiting**: 과도한 요청 차단

**Application - Django API**:
- **REST API**: 클라이언트와 데이터 통신
- **ORM**: PostgreSQL 데이터베이스 접근
- **인증**: JWT 토큰 기반
- **연동**: Slack 알림 전송

**Application - React Frontend**:
- **SPA**: Single Page Application
- **빌드**: Nginx가 정적 파일로 서빙
- **Code Splitting**: 21개 페이지 lazy loading

**Application - Celery Worker**:
- **비동기 작업**: 이메일 발송, DB 백업, AI 요청
- **스케줄러**: Celery Beat로 매일 정해진 시간 실행
- **메시지 브로커**: Redis 사용

**Data Layer - PostgreSQL**:
- **메인 데이터베이스**: 사용자, 콘텐츠, 리뷰 등 모든 데이터
- **버전**: PostgreSQL 15
- **백업**: pg_dump로 매일 S3에 저장

**Data Layer - Redis**:
- **캐시**: 자주 조회하는 데이터 임시 저장
- **세션**: 로그인 세션 관리
- **메시지 큐**: Celery 작업 큐

**Slack**:
- **모니터링 알림**: 에러 발생, 백업 성공/실패
- **배포 알림**: GitHub Actions 배포 결과

---

## 전체 플로우

### 사용자 요청 처리
```
1. 사용자가 브라우저에서 접속
2. Cloudflare가 SSL로 암호화
3. EC2 서버로 전달
4. Nginx가 요청 종류 판단:
   - API 요청 → Django 처리
   - 페이지 요청 → React 파일 전송
5. Django가 PostgreSQL에서 데이터 조회
6. Redis 캐시 확인 (있으면 빠른 응답)
7. 결과를 사용자에게 반환
```

### 백그라운드 작업
```
1. Celery Beat가 매일 3시에 작업 예약
2. Celery Worker가 작업 수행:
   - PostgreSQL 백업 → S3 업로드
   - 이메일 발송
3. 작업 결과를 Slack으로 알림
```

### 배포 프로세스
```
1. 개발자가 코드 푸시 (git push)
2. GitHub Actions 자동 실행
3. SSH로 EC2 접속
4. deploy.sh 실행:
   - git pull (최신 코드)
   - docker-compose build (이미지 빌드)
   - docker-compose up -d (서비스 재시작)
5. 배포 완료 → Slack 알림
```

---

## 핵심 설계 원칙

**1. 비용 최적화**
- RDS 대신 Docker PostgreSQL (월 $30 절약)
- ElastiCache 대신 Docker Redis (월 $25 절약)
- Cloudflare 무료 플랜 (ALB $16 절약)

**2. 단순성**
- 하나의 EC2에서 모든 서비스 실행
- Docker Compose로 간단한 관리
- 복잡한 네트워크 설정 최소화

**3. 확장 가능성**
- VPC 구조로 나중에 Multi-AZ 전환 가능
- Docker 기반이라 쿠버네티스 전환 쉬움
- S3 백업으로 RDS 마이그레이션 준비됨

**4. 운영 편의성**
- Slack 알림으로 실시간 모니터링
- 자동 백업으로 데이터 안전성
- GitHub Actions로 배포 자동화
