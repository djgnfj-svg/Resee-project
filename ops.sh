#!/bin/bash

# 🚀 Resee 운영 관리 통합 스크립트
# 모든 운영 작업을 하나의 스크립트로 통합

set -e

# 설정
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/resee_ops.log"

# 로그 함수
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 도움말
show_help() {
    cat << EOF
🚀 Resee 운영 관리 도구

사용법: ./ops.sh <명령어> [옵션]

📋 주요 명령어:
  deploy          프로덕션 배포
  backup          백업 실행
  restore         백업 복원
  health          시스템 상태 확인
  maintain        유지보수 실행
  logs            로그 관리

🔧 상세 명령어:
  deploy [--force] [--skip-backup]
                  프로덕션 배포 실행
                  --force: 확인 없이 배포
                  --skip-backup: 배업 생략

  backup [daily|weekly|monthly]
                  백업 실행 (기본: daily)

  restore [daily|weekly|monthly] [날짜]
                  백업 복원
                  예: ./ops.sh restore daily 20250122_143000

  health [--detailed] [--json]
                  시스템 상태 확인
                  --detailed: 상세 정보
                  --json: JSON 출력

  maintain db     데이터베이스 최적화
  maintain logs   로그 정리
  maintain all    전체 유지보수

  logs view       최근 로그 확인
  logs clean      로그 정리
  logs errors     오늘 오류 로그 확인

📊 추가 명령어:
  status          간단한 상태 확인
  start           서비스 시작
  stop            서비스 중지
  restart         서비스 재시작

예시:
  ./ops.sh deploy --force
  ./ops.sh backup daily
  ./ops.sh health --detailed
  ./ops.sh maintain all

EOF
}

# 간단한 상태 확인
quick_status() {
    echo "🔍 Resee 서비스 상태:"
    echo "----------------------------------------"
    
    # Docker 서비스 확인
    local running=0
    local total=0
    local services=("resee-db-1" "resee-redis-1" "resee-backend-1" "resee-frontend-1" "resee-nginx-1")
    
    for service in "${services[@]}"; do
        ((total++))
        if docker ps --format "{{.Names}}" | grep -q "^${service}$"; then
            echo "✅ $service"
            ((running++))
        else
            echo "❌ $service"
        fi
    done
    
    echo "----------------------------------------"
    echo "실행 중: $running/$total"
    
    # 간단한 헬스체크
    if [ "$running" -eq "$total" ]; then
        if curl -s http://localhost/api/health/ >/dev/null 2>&1; then
            echo "🟢 전체 시스템 정상"
        else
            echo "🟡 서비스는 실행 중이나 응답 없음"
        fi
    else
        echo "🔴 일부 서비스 중지됨"
    fi
}

# 프로덕션 배포
deploy_production() {
    log "🚀 프로덕션 배포 시작"
    
    local force=false
    local skip_backup=false
    
    # 옵션 처리
    for arg in "$@"; do
        case $arg in
            --force) force=true ;;
            --skip-backup) skip_backup=true ;;
        esac
    done
    
    # 환경 파일 확인
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        echo "❌ .env.production 파일이 없습니다!"
        echo "   .env.production.template를 복사해서 만드세요."
        exit 1
    fi
    
    # 확인 (force 옵션이 아닌 경우)
    if [ "$force" != true ]; then
        echo "⚠️  프로덕션 배포를 시작합니다."
        read -p "계속하시겠습니까? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "배포 취소됨"
            exit 0
        fi
    fi
    
    # 백업 실행 (skip 옵션이 아닌 경우)
    if [ "$skip_backup" != true ]; then
        echo "🔄 배포 전 백업 실행 중..."
        do_backup daily
    fi
    
    # 기존 서비스 중지
    echo "🛑 기존 서비스 중지 중..."
    docker-compose -f docker-compose.production.yml down --timeout 30 || true
    
    # 이미지 빌드
    echo "🔨 프로덕션 이미지 빌드 중..."
    docker-compose -f docker-compose.production.yml build --no-cache --pull
    
    # 데이터베이스 마이그레이션
    echo "🗃️ 데이터베이스 마이그레이션..."
    docker-compose -f docker-compose.production.yml up -d db redis
    sleep 30
    docker-compose -f docker-compose.production.yml run --rm backend python manage.py migrate --noinput
    docker-compose -f docker-compose.production.yml run --rm backend python manage.py collectstatic --noinput
    
    # 서비스 시작
    echo "▶️ 서비스 시작 중..."
    docker-compose -f docker-compose.production.yml up -d
    
    # 헬스체크 대기
    echo "🔍 서비스 헬스체크 중..."
    local attempt=1
    local max_attempts=30
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost/api/health/ >/dev/null 2>&1; then
            echo "✅ 배포 완료! ($attempt초 후 서비스 응답)"
            echo "🌐 서비스 URL: http://localhost"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ 배포 실패: 서비스가 응답하지 않습니다"
            return 1
        fi
        
        echo "   대기 중... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}

# 백업 실행
do_backup() {
    local backup_type=${1:-daily}
    
    log "💾 백업 시작 ($backup_type)"
    
    # PostgreSQL 백업
    echo "📊 PostgreSQL 백업 중..."
    mkdir -p /backups/postgresql/$backup_type
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local pg_backup="/backups/postgresql/$backup_type/resee_${backup_type}_${timestamp}.sql.gz"
    
    docker exec resee-db-1 pg_dump -U resee_user -d resee_db --no-password | gzip > "$pg_backup"
    
    if [ $? -eq 0 ]; then
        echo "✅ PostgreSQL 백업 완료: $(du -h "$pg_backup" | cut -f1)"
    else
        echo "❌ PostgreSQL 백업 실패"
        return 1
    fi
    
    # Redis 백업
    echo "🔴 Redis 백업 중..."
    mkdir -p /backups/redis/$backup_type
    
    local redis_backup="/backups/redis/$backup_type/redis_${backup_type}_${timestamp}.rdb.gz"
    
    docker exec resee-redis-1 redis-cli BGSAVE >/dev/null
    sleep 3
    docker cp resee-redis-1:/data/dump.rdb /tmp/dump_${timestamp}.rdb
    gzip /tmp/dump_${timestamp}.rdb
    mv /tmp/dump_${timestamp}.rdb.gz "$redis_backup"
    
    echo "✅ Redis 백업 완료: $(du -h "$redis_backup" | cut -f1)"
    
    # 오래된 백업 정리
    case $backup_type in
        daily) find /backups -name "*daily*.gz" -mtime +7 -delete ;;
        weekly) find /backups -name "*weekly*.gz" -mtime +28 -delete ;;
        monthly) find /backups -name "*monthly*.gz" -mtime +365 -delete ;;
    esac
    
    echo "🧹 오래된 백업 정리 완료"
    log "백업 완료 ($backup_type)"
}

# 백업 복원
do_restore() {
    local backup_type=${1:-daily}
    local backup_date=${2}
    
    echo "⚠️  백업 복원은 현재 데이터를 덮어씁니다!"
    read -p "정말로 복원하시겠습니까? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "복원 취소됨"
        return 0
    fi
    
    log "🔄 백업 복원 시작 ($backup_type)"
    
    # 백업 파일 찾기
    local pg_backup
    local redis_backup
    
    if [ -n "$backup_date" ]; then
        pg_backup=$(find "/backups/postgresql/$backup_type" -name "*${backup_date}*.sql.gz" | head -1)
        redis_backup=$(find "/backups/redis/$backup_type" -name "*${backup_date}*.rdb.gz" | head -1)
    else
        pg_backup=$(find "/backups/postgresql/$backup_type" -name "*.sql.gz" | sort | tail -1)
        redis_backup=$(find "/backups/redis/$backup_type" -name "*.rdb.gz" | sort | tail -1)
    fi
    
    if [ -z "$pg_backup" ]; then
        echo "❌ PostgreSQL 백업 파일을 찾을 수 없습니다"
        return 1
    fi
    
    echo "📊 PostgreSQL 복원 중: $pg_backup"
    gunzip -c "$pg_backup" | docker exec -i resee-db-1 psql -U resee_user -d resee_db
    
    if [ -n "$redis_backup" ]; then
        echo "🔴 Redis 복원 중: $redis_backup"
        docker stop resee-redis-1
        gunzip -c "$redis_backup" > /tmp/restore_dump.rdb
        docker cp /tmp/restore_dump.rdb resee-redis-1:/data/dump.rdb
        rm /tmp/restore_dump.rdb
        docker start resee-redis-1
    fi
    
    echo "✅ 복원 완료!"
    log "백업 복원 완료"
}

# 헬스체크
do_health() {
    local detailed=false
    local json_output=false
    
    for arg in "$@"; do
        case $arg in
            --detailed) detailed=true ;;
            --json) json_output=true ;;
        esac
    done
    
    if [ "$json_output" = true ]; then
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"status\": \"checking\""
        echo "}"
        return 0
    fi
    
    echo "🏥 시스템 헬스체크"
    echo "========================================"
    
    # 기본 정보
    echo "💻 시스템 정보:"
    echo "   업타임: $(uptime -p 2>/dev/null || uptime | cut -d',' -f1)"
    echo "   로드: $(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1)"
    
    # 리소스 사용률
    local memory_usage=$(free | grep '^Mem:' | awk '{printf "%.1f", ($3/$2)*100}')
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    echo "   메모리: ${memory_usage}%"
    echo "   디스크: ${disk_usage}%"
    
    # 서비스 상태
    echo ""
    echo "🐳 Docker 서비스:"
    local services=("db" "redis" "backend" "frontend" "nginx" "celery")
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "$service.*Up"; then
            echo "   ✅ $service"
        else
            echo "   ❌ $service"
        fi
    done
    
    # 웹 서비스 응답
    echo ""
    echo "🌐 웹 서비스:"
    if curl -s http://localhost/api/health/ >/dev/null 2>&1; then
        echo "   ✅ API 서버"
    else
        echo "   ❌ API 서버"
    fi
    
    if curl -s http://localhost/ >/dev/null 2>&1; then
        echo "   ✅ 프론트엔드"
    else
        echo "   ❌ 프론트엔드"
    fi
    
    # 상세 정보
    if [ "$detailed" = true ]; then
        echo ""
        echo "📊 상세 정보:"
        echo "   프로세스: $(ps aux | wc -l)"
        echo "   네트워크: $(ss -t | wc -l) connections"
        
        # 최근 백업 확인
        local recent_backups=$(find /backups -name "*.gz" -mtime -1 2>/dev/null | wc -l)
        echo "   최근 백업: $recent_backups (24시간 내)"
        
        # 로그 오류 확인
        local log_errors=$(find /var/log -name "*.log" -mtime -1 -exec grep -l "ERROR\|CRITICAL\|FATAL" {} \; 2>/dev/null | wc -l)
        echo "   로그 오류: $log_errors files"
    fi
    
    echo "========================================"
}

# 유지보수
do_maintenance() {
    local task=${1:-all}
    
    case $task in
        db)
            echo "🗃️ 데이터베이스 최적화 중..."
            docker exec resee-db-1 psql -U resee_user -d resee_db -c "VACUUM ANALYZE;"
            echo "✅ 데이터베이스 최적화 완료"
            ;;
        logs)
            echo "📝 로그 정리 중..."
            # 1주일 이상된 로그 압축
            find /var/log -name "*.log" -mtime +7 -not -name "*.gz" -exec gzip {} \; 2>/dev/null || true
            # 1달 이상된 압축 로그 삭제
            find /var/log -name "*.log.gz" -mtime +30 -delete 2>/dev/null || true
            
            # Docker 로그 정리
            docker system prune -f >/dev/null 2>&1 || true
            echo "✅ 로그 정리 완료"
            ;;
        all)
            echo "🔧 전체 유지보수 실행 중..."
            do_maintenance db
            do_maintenance logs
            echo "✅ 전체 유지보수 완료"
            ;;
        *)
            echo "❌ 알 수 없는 유지보수 작업: $task"
            echo "사용 가능: db, logs, all"
            return 1
            ;;
    esac
    
    log "유지보수 완료: $task"
}

# 로그 관리
manage_logs() {
    local action=${1:-view}
    
    case $action in
        view)
            echo "📋 최근 로그 (마지막 50줄):"
            echo "========================================"
            docker-compose -f docker-compose.production.yml logs --tail=50
            ;;
        clean)
            do_maintenance logs
            ;;
        errors)
            echo "🚨 오늘 오류 로그:"
            echo "========================================"
            local today=$(date +%Y-%m-%d)
            grep "$today" /var/log/*.log 2>/dev/null | grep -E "ERROR|CRITICAL|FATAL" | head -20 || echo "오류 로그 없음"
            ;;
        *)
            echo "❌ 알 수 없는 로그 작업: $action"
            echo "사용 가능: view, clean, errors"
            return 1
            ;;
    esac
}

# 서비스 제어
control_services() {
    local action=$1
    
    case $action in
        start)
            echo "▶️ 서비스 시작 중..."
            docker-compose -f docker-compose.production.yml up -d
            ;;
        stop)
            echo "⏹️ 서비스 중지 중..."
            docker-compose -f docker-compose.production.yml down
            ;;
        restart)
            echo "🔄 서비스 재시작 중..."
            docker-compose -f docker-compose.production.yml restart
            ;;
        *)
            echo "❌ 알 수 없는 서비스 작업: $action"
            echo "사용 가능: start, stop, restart"
            return 1
            ;;
    esac
    
    echo "✅ $action 완료"
}

# 메인 실행 함수
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    local command=$1
    shift
    
    case $command in
        deploy)
            deploy_production "$@"
            ;;
        backup)
            do_backup "$@"
            ;;
        restore)
            do_restore "$@"
            ;;
        health)
            do_health "$@"
            ;;
        maintain)
            do_maintenance "$@"
            ;;
        logs)
            manage_logs "$@"
            ;;
        status)
            quick_status
            ;;
        start|stop|restart)
            control_services "$command"
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            echo "❌ 알 수 없는 명령어: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"