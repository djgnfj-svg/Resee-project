# Resee 운영 관리 가이드

## 📋 개요

이 가이드는 Resee 애플리케이션의 프로덕션 환경 운영을 위한 종합적인 운영 관리 방법을 제공합니다.

## 🚀 프로덕션 배포

### 초기 배포

1. **환경 설정 준비**
   ```bash
   # .env.production.template를 복사하여 실제 환경 설정
   cp .env.production.template .env.production
   
   # 환경 변수 편집 (중요한 값들 모두 변경 필요)
   nano .env.production
   ```

2. **프로덕션 배포 실행**
   ```bash
   # 배포 스크립트 실행
   ./scripts/deploy/deploy_production.sh
   
   # 강제 배포 (확인 없이)
   ./scripts/deploy/deploy_production.sh --force
   
   # 백업 생략하고 배포
   ./scripts/deploy/deploy_production.sh --skip-backup
   ```

3. **배포 후 확인**
   ```bash
   # 시스템 상태 확인
   ./scripts/monitoring/system_health_check.sh --detailed
   
   # 서비스 상태 확인
   docker-compose -f docker-compose.production.yml ps
   ```

### 업데이트 배포

```bash
# Git 최신 코드 받기
git pull origin main

# 프로덕션 배포
./scripts/deploy/deploy_production.sh
```

## 🔄 백업 및 복원

### 자동 백업 설정

1. **백업 스크립트 권한 확인**
   ```bash
   ls -la scripts/backup/
   chmod +x scripts/backup/*.sh
   ```

2. **Crontab 설정** (자동화)
   ```bash
   # crontab 편집
   crontab -e
   
   # 다음 내용 추가
   # 매일 새벽 2시 전체 백업
   0 2 * * * /path/to/resee/scripts/backup/full_backup.sh daily >> /var/log/cron_backup.log 2>&1
   
   # 매주 일요일 새벽 1시 주간 백업
   0 1 * * 0 /path/to/resee/scripts/backup/full_backup.sh weekly >> /var/log/cron_backup.log 2>&1
   
   # 매월 1일 새벽 12시 월간 백업
   0 0 1 * * /path/to/resee/scripts/backup/full_backup.sh monthly >> /var/log/cron_backup.log 2>&1
   ```

### 수동 백업

```bash
# 전체 백업 (PostgreSQL + Redis + 설정 파일)
./scripts/backup/full_backup.sh daily

# PostgreSQL만 백업
./scripts/backup/postgresql_backup.sh daily

# Redis만 백업
./scripts/backup/redis_backup.sh daily
```

### 백업 복원

```bash
# 최신 백업으로 복원
./scripts/backup/restore_backup.sh daily

# 특정 날짜 백업으로 복원
./scripts/backup/restore_backup.sh daily 20250122_143000

# 도움말 확인
./scripts/backup/restore_backup.sh --help
```

## 🔧 시스템 유지보수

### 데이터베이스 유지보수

```bash
# 기본 유지보수 (VACUUM, ANALYZE, REINDEX)
./scripts/maintenance/db_maintenance.sh

# 전체 VACUUM (더 오래 걸리지만 효과적)
./scripts/maintenance/db_maintenance.sh --vacuum-full

# 통계 분석만 실행
./scripts/maintenance/db_maintenance.sh --analyze-only
```

**권장 실행 주기:**
- 기본 유지보수: 매주
- 전체 VACUUM: 매월
- 통계 분석: 매일

### 로그 정리

```bash
# 로그 정리 및 압축
./scripts/maintenance/log_cleanup.sh

# 실제 삭제 전 시뮬레이션
./scripts/maintenance/log_cleanup.sh --dry-run

# 강제 정리 (확인 없이)
./scripts/maintenance/log_cleanup.sh --force-cleanup
```

**자동화 설정:**
```bash
# 매일 새벽 3시 로그 정리
0 3 * * * /path/to/resee/scripts/maintenance/log_cleanup.sh >> /var/log/log_cleanup.log 2>&1
```

## 📊 모니터링

### 시스템 상태 확인

```bash
# 기본 헬스체크
./scripts/monitoring/system_health_check.sh

# 상세 정보 포함
./scripts/monitoring/system_health_check.sh --detailed

# JSON 출력 (API 연동용)
./scripts/monitoring/system_health_check.sh --json

# 알림 모드 (임계값 초과시 알림 전송)
./scripts/monitoring/system_health_check.sh --alert
```

### 주요 모니터링 지표

| 항목 | 임계값 | 설명 |
|------|--------|------|
| CPU 사용률 | 80% | 지속적 초과시 스케일업 필요 |
| 메모리 사용률 | 85% | 메모리 부족 경고 |
| 디스크 사용률 | 90% | 즉시 정리 필요 |
| 시스템 로드 | 5.0 | 시스템 과부하 |
| API 응답시간 | 5초 | 성능 저하 |

### 알림 설정

1. **Slack 알림** (.env.production에 추가)
   ```bash
   BACKUP_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/slack/webhook
   ```

2. **이메일 알림** (.env.production에 추가)
   ```bash
   BACKUP_EMAIL_NOTIFICATIONS=admin@your-domain.com
   ```

## 🛡️ 보안 관리

### SSL/TLS 설정

1. **Let's Encrypt 인증서 설치**
   ```bash
   # Certbot 설치
   sudo apt install certbot python3-certbot-nginx
   
   # 인증서 발급
   sudo certbot --nginx -d your-domain.com
   ```

2. **SSL 설정 활성화**
   ```bash
   # .env.production 파일 편집
   USE_TLS=True
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

3. **Nginx SSL 설정 활성화**
   ```bash
   # config/nginx.production.conf에서 SSL 블록 주석 해제
   nano config/nginx.production.conf
   ```

### 보안 점검

```bash
# 기본 보안 상태 확인 (헬스체크에 포함)
./scripts/monitoring/system_health_check.sh --detailed

# 환경 파일 권한 확인
ls -la .env*
chmod 600 .env.production  # 필요시 권한 수정

# 실패한 로그인 시도 확인
grep "Failed password" /var/log/auth.log | grep "$(date +%Y-%m-%d)"
```

## 📈 성능 최적화

### 데이터베이스 최적화

1. **인덱스 상태 확인**
   ```bash
   docker exec resee-db-1 psql -U resee_user -d resee_db -c "
   SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch,
          CASE WHEN idx_tup_read > 0 
               THEN round((idx_tup_fetch::float / idx_tup_read::float) * 100, 2)
               ELSE 0 END as hit_rate_percentage
   FROM pg_stat_user_indexes 
   ORDER BY hit_rate_percentage ASC LIMIT 10;"
   ```

2. **슬로우 쿼리 모니터링**
   ```bash
   # PostgreSQL에서 슬로우 쿼리 활성화
   docker exec resee-db-1 psql -U resee_user -d resee_db -c "
   ALTER SYSTEM SET log_min_duration_statement = '1000';  -- 1초 이상 쿼리 로깅
   SELECT pg_reload_conf();"
   ```

### 캐시 최적화

```bash
# Redis 메모리 사용률 확인
docker exec resee-redis-1 redis-cli info memory

# 캐시 히트율 확인
docker exec resee-redis-1 redis-cli info stats | grep keyspace
```

### 리소스 사용률 모니터링

```bash
# Docker 컨테이너별 리소스 사용률
docker stats --no-stream

# 시스템 전체 리소스 사용률
htop  # 또는
top
```

## 🚨 장애 대응

### 긴급 상황 체크리스트

1. **서비스 다운시**
   ```bash
   # 서비스 상태 확인
   docker-compose -f docker-compose.production.yml ps
   
   # 로그 확인
   docker-compose -f docker-compose.production.yml logs --tail=100
   
   # 서비스 재시작
   docker-compose -f docker-compose.production.yml restart
   ```

2. **데이터베이스 장애**
   ```bash
   # 데이터베이스 상태 확인
   docker exec resee-db-1 pg_isready -U resee_user
   
   # 연결 수 확인
   docker exec resee-db-1 psql -U resee_user -d resee_db -c "SELECT count(*) FROM pg_stat_activity;"
   
   # 필요시 백업에서 복원
   ./scripts/backup/restore_backup.sh daily
   ```

3. **디스크 공간 부족**
   ```bash
   # 로그 강제 정리
   ./scripts/maintenance/log_cleanup.sh --force-cleanup
   
   # Docker 이미지 정리
   docker system prune -a -f
   
   # 오래된 백업 수동 삭제
   find /backups -name "*.gz" -mtime +30 -delete
   ```

### 롤백 절차

```bash
# 1. 서비스 중지
docker-compose -f docker-compose.production.yml down

# 2. 백업에서 복원
./scripts/backup/restore_backup.sh daily [backup_date]

# 3. 이전 버전으로 코드 롤백 (Git)
git checkout [previous_commit]

# 4. 이전 버전으로 배포
./scripts/deploy/deploy_production.sh --force
```

## 📋 정기 작업 체크리스트

### 일일 작업
- [ ] 시스템 상태 확인 (`system_health_check.sh`)
- [ ] 로그 오류 확인
- [ ] 백업 상태 확인
- [ ] 디스크 사용량 확인

### 주간 작업
- [ ] 데이터베이스 유지보수 (`db_maintenance.sh`)
- [ ] 로그 정리 (`log_cleanup.sh`)
- [ ] 보안 업데이트 확인
- [ ] 성능 지표 검토

### 월간 작업
- [ ] 전체 VACUUM 실행
- [ ] SSL 인증서 만료일 확인
- [ ] 백업 복원 테스트
- [ ] 시스템 업데이트
- [ ] 용량 계획 검토

## 🔧 트러블슈팅

### 자주 발생하는 문제들

1. **"No space left on device" 오류**
   ```bash
   # 디스크 사용량 확인
   df -h
   
   # 로그 정리
   ./scripts/maintenance/log_cleanup.sh --force-cleanup
   
   # Docker 정리
   docker system prune -a -f
   ```

2. **데이터베이스 연결 오류**
   ```bash
   # 연결 테스트
   docker exec resee-db-1 pg_isready -U resee_user
   
   # 연결 수 확인
   docker exec resee-db-1 psql -U resee_user -d resee_db -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
   
   # 필요시 데이터베이스 재시작
   docker restart resee-db-1
   ```

3. **높은 메모리 사용률**
   ```bash
   # 메모리 사용량 확인
   free -h
   
   # 프로세스별 메모리 사용량
   ps aux --sort=-%mem | head -10
   
   # Docker 컨테이너별 메모리 사용량
   docker stats --no-stream
   ```

## 📞 지원 및 연락처

- **기술 지원**: [기술팀 이메일]
- **운영 알림**: [운영팀 Slack 채널]
- **긴급 연락**: [긴급 연락처]

---

**중요**: 이 가이드의 모든 스크립트와 절차는 프로덕션 환경에 적용하기 전에 개발/스테이징 환경에서 먼저 테스트해야 합니다.