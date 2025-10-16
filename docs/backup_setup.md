# 자동 백업 시스템 설정 가이드

## 개요
Resee 프로젝트의 자동 데이터베이스 백업 시스템 설정 방법입니다.

## 백업 스크립트 특징

### 기본 기능
- PostgreSQL 데이터베이스 백업 (gzip 압축)
- 30일 보관 정책 (오래된 백업 자동 삭제)
- 백업 파일 무결성 검증
- 환경별 백업 (production/development)
- 타임스탬프 기반 파일명

### 고급 기능
- **Slack 알림**: 백업 성공/실패 시 Slack으로 알림
- **S3 업로드**: AWS S3에 자동 업로드 (선택사항)
- **로깅**: 타임스탬프가 포함된 상세 로그

## 사용 방법

### 수동 백업
```bash
# Development 환경 백업
bash scripts/backup_db.sh development

# Production 환경 백업
bash scripts/backup_db.sh production
```

### 환경 변수 설정

**필수 환경 변수** (`.env.prod`):
```bash
# Slack 알림 (선택사항)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# S3 업로드 (선택사항)
AWS_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Cron 설정

### 1. Crontab 편집
```bash
crontab -e
```

### 2. Cron Job 추가

**매일 새벽 3시 자동 백업** (권장):
```bash
# Production 백업 (매일 새벽 3시)
0 3 * * * cd /home/djgnf/projects/Resee-project && bash scripts/backup_db.sh production >> logs/backup.log 2>&1

# Development 백업 (매주 일요일 새벽 4시)
0 4 * * 0 cd /home/djgnf/projects/Resee-project && bash scripts/backup_db.sh development >> logs/backup.log 2>&1
```

**설정 설명**:
- `0 3 * * *`: 매일 새벽 3시 (분 시 일 월 요일)
- `cd /path/to/project`: 프로젝트 디렉토리로 이동
- `>> logs/backup.log 2>&1`: 로그 파일에 출력 저장

### 3. Cron 서비스 확인
```bash
# Cron 서비스 상태 확인
sudo systemctl status cron

# Cron 서비스 시작 (필요시)
sudo systemctl start cron
sudo systemctl enable cron
```

### 4. Cron 작업 확인
```bash
# 현재 설정된 cron job 확인
crontab -l

# Cron 로그 확인
grep CRON /var/log/syslog
```

## 백업 복구

### 복구 스크립트 사용
```bash
# 최신 백업 복구
bash scripts/restore_db.sh

# 특정 백업 파일 복구
bash scripts/restore_db.sh backups/resee_production_20250115_030000.sql.gz
```

### 수동 복구
```bash
# 백업 파일 압축 해제 및 복원
gunzip < backups/resee_production_20250115_030000.sql.gz | \
  docker-compose exec -T postgres psql -U postgres -d resee_prod
```

## S3 업로드 설정 (선택사항)

### 1. AWS CLI 설치
```bash
# Ubuntu/Debian
sudo apt-get install awscli

# macOS
brew install awscli
```

### 2. AWS 자격 증명 설정
```bash
aws configure
# AWS Access Key ID: 입력
# AWS Secret Access Key: 입력
# Default region: ap-northeast-2 (서울)
# Default output format: json
```

### 3. S3 버킷 생성
```bash
# S3 버킷 생성
aws s3 mb s3://resee-backups --region ap-northeast-2

# Lifecycle 정책 설정 (90일 후 삭제)
aws s3api put-bucket-lifecycle-configuration \
  --bucket resee-backups \
  --lifecycle-configuration file://s3-lifecycle.json
```

**s3-lifecycle.json**:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Prefix": "backups/database/",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

## 모니터링

### 백업 로그 확인
```bash
# 백업 로그 실시간 확인
tail -f logs/backup.log

# 최근 백업 상태 확인
tail -20 logs/backup.log
```

### 백업 파일 확인
```bash
# 로컬 백업 파일 목록
ls -lh backups/resee_production_*.sql.gz

# S3 백업 파일 목록 (S3 사용 시)
aws s3 ls s3://resee-backups/backups/database/
```

### Slack 알림 확인
백업 성공/실패 시 자동으로 Slack 알림이 전송됩니다:
- ✅ 성공: 파일명, 크기, 환경 정보
- ❌ 실패: 실패 원인 및 환경 정보

## 트러블슈팅

### 백업 실패 시
1. **Docker 컨테이너 상태 확인**:
   ```bash
   docker-compose ps
   ```

2. **PostgreSQL 연결 확인**:
   ```bash
   docker-compose exec postgres psql -U postgres -l
   ```

3. **디스크 공간 확인**:
   ```bash
   df -h
   ```

4. **권한 확인**:
   ```bash
   ls -la backups/
   chmod +x scripts/backup_db.sh
   ```

### Cron이 실행되지 않을 때
1. **Cron 서비스 확인**:
   ```bash
   sudo systemctl status cron
   ```

2. **Cron 로그 확인**:
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

3. **환경 변수 확인**:
   Cron 환경에서는 환경 변수가 로드되지 않을 수 있습니다.
   Crontab에 직접 환경 변수를 설정하거나, 스크립트에서 `.env` 파일을 로드하세요.

## 보안 권장사항

1. **백업 파일 암호화** (선택사항):
   ```bash
   gpg --symmetric --cipher-algo AES256 backup.sql.gz
   ```

2. **S3 버킷 암호화**:
   AWS S3에서 서버 측 암호화(SSE) 활성화

3. **접근 제한**:
   ```bash
   chmod 700 backups/
   chmod 600 backups/*.sql.gz
   ```

4. **정기적인 복구 테스트**:
   최소 월 1회 백업 복구 테스트 수행

## 참고

- 백업 파일 위치: `./backups/`
- 보관 기간: 30일
- 백업 형식: PostgreSQL dump (gzip 압축)
- S3 스토리지 클래스: STANDARD_IA (저빈도 액세스)
- 로그 파일: `logs/backup.log`
