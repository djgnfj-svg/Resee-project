#!/bin/bash

# 🗄️ Resee 데이터베이스 백업 스크립트
# 매일 자동 실행되어 PostgreSQL 데이터베이스를 백업합니다.

set -e  # 에러 발생 시 스크립트 중단

# 설정
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="resee_backup_${DATE}.sql"
LOG_FILE="/var/log/resee/backup.log"
COMPOSE_FILE="/opt/Resee/docker-compose.production.yml"

# 환경 변수 로드
if [ -f "/opt/Resee/.env.production" ]; then
    source /opt/Resee/.env.production
else
    echo "$(date): ERROR - 환경 변수 파일을 찾을 수 없습니다." >> "$LOG_FILE"
    exit 1
fi

# 로그 함수
log_message() {
    echo "$(date): $1" >> "$LOG_FILE"
    echo "$1"
}

log_message "데이터베이스 백업을 시작합니다..."

# 백업 디렉토리 확인 및 생성
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    log_message "백업 디렉토리 생성: $BACKUP_DIR"
fi

cd /opt/Resee

# Docker 컨테이너 상태 확인
if ! docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
    log_message "ERROR - 데이터베이스 컨테이너가 실행 중이지 않습니다."
    exit 1
fi

# PostgreSQL 백업 실행
log_message "PostgreSQL 백업 중... (파일: ${BACKUP_FILE})"

if docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
    -U "${POSTGRES_USER:-resee_prod_user}" \
    "${POSTGRES_DB:-resee_production}" > "${BACKUP_DIR}/${BACKUP_FILE}"; then
    
    # 백업 파일 압축
    log_message "백업 파일 압축 중..."
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    
    # 백업 파일 크기 확인
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)
    log_message "백업 완료: ${BACKUP_FILE}.gz (크기: ${BACKUP_SIZE})"
    
    # 백업 파일 권한 설정
    chmod 600 "${BACKUP_DIR}/${BACKUP_FILE}.gz"
    
else
    log_message "ERROR - 데이터베이스 백업에 실패했습니다."
    exit 1
fi

# 오래된 백업 파일 정리 (7일 이상)
log_message "오래된 백업 파일 정리 중..."
OLD_BACKUPS=$(find "${BACKUP_DIR}" -name "resee_backup_*.sql.gz" -mtime +7)

if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r file; do
        if [ -f "$file" ]; then
            rm "$file"
            log_message "삭제된 오래된 백업: $(basename "$file")"
        fi
    done
else
    log_message "삭제할 오래된 백업 파일이 없습니다."
fi

# 백업 상태 요약
TOTAL_BACKUPS=$(ls -1 "${BACKUP_DIR}"/resee_backup_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)

log_message "백업 상태 요약:"
log_message "- 총 백업 파일 수: ${TOTAL_BACKUPS}개"
log_message "- 백업 디렉토리 총 크기: ${TOTAL_SIZE}"
log_message "- 최신 백업: ${BACKUP_FILE}.gz"

# 디스크 사용량 확인
DISK_USAGE=$(df "${BACKUP_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log_message "WARNING - 디스크 사용량이 높습니다 (${DISK_USAGE}%). 백업 파일을 정리하세요."
fi

# Redis 백업 (선택사항)
if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
    REDIS_BACKUP_DIR="/backups/redis"
    mkdir -p "$REDIS_BACKUP_DIR"
    
    log_message "Redis 백업 중..."
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE; then
        # Redis 백업 파일 복사
        sleep 5  # BGSAVE 완료 대기
        docker-compose -f "$COMPOSE_FILE" exec -T redis cat /data/dump.rdb > "${REDIS_BACKUP_DIR}/redis_backup_${DATE}.rdb"
        gzip "${REDIS_BACKUP_DIR}/redis_backup_${DATE}.rdb"
        log_message "Redis 백업 완료: redis_backup_${DATE}.rdb.gz"
        
        # 오래된 Redis 백업 정리
        find "${REDIS_BACKUP_DIR}" -name "redis_backup_*.rdb.gz" -mtime +7 -delete
    else
        log_message "WARNING - Redis 백업에 실패했습니다."
    fi
fi

# 백업 검증 (간단한 무결성 체크)
log_message "백업 파일 무결성 검증 중..."
if gunzip -t "${BACKUP_DIR}/${BACKUP_FILE}.gz" 2>/dev/null; then
    log_message "백업 파일 무결성 검증 통과"
else
    log_message "ERROR - 백업 파일이 손상되었습니다!"
    exit 1
fi

# 성공 완료
log_message "모든 백업 작업이 성공적으로 완료되었습니다."

# 백업 성공 알림 (선택사항 - 이메일 또는 웹훅)
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"Resee DB 백업 완료: ${BACKUP_FILE}.gz (${BACKUP_SIZE})\"}" \
        2>/dev/null || true
fi

exit 0