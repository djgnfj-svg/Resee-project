#!/bin/bash

# Comprehensive Backup Manager for Resee Project
# Manages both database and user data backups with scheduling

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${SCRIPT_DIR}/../backups"
DB_BACKUP_DIR="${BACKUP_ROOT}/postgresql"
USER_DATA_BACKUP_DIR="${BACKUP_ROOT}/user_data"
LOGS_DIR="${BACKUP_ROOT}/logs"
CONFIG_FILE="${SCRIPT_DIR}/backup_config.json"

# Create directories
mkdir -p "${DB_BACKUP_DIR}" "${USER_DATA_BACKUP_DIR}" "${LOGS_DIR}"

# Function to log messages
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOGS_DIR}/backup_manager.log"
}

# Function to create default config
create_default_config() {
    cat > "${CONFIG_FILE}" << 'EOF'
{
    "backup_config": {
        "database": {
            "enabled": true,
            "schedule": {
                "daily": true,
                "weekly": true,
                "monthly": true
            },
            "retention": {
                "daily_backups_keep": 7,
                "weekly_backups_keep": 4,
                "monthly_backups_keep": 12
            }
        },
        "user_data": {
            "enabled": true,
            "schedule": {
                "daily": true,
                "weekly": true
            },
            "retention": {
                "daily_backups_keep": 7,
                "weekly_backups_keep": 8
            },
            "compress": true
        },
        "notifications": {
            "slack_webhook": "",
            "email_recipients": [],
            "notify_on_success": false,
            "notify_on_failure": true
        },
        "health_checks": {
            "test_restore": false,
            "verify_integrity": true,
            "max_backup_age_hours": 26
        }
    }
}
EOF
    log "INFO" "Default configuration created at ${CONFIG_FILE}"
}

# Function to read config
read_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        create_default_config
    fi

    if ! command -v jq >/dev/null 2>&1; then
        log "ERROR" "jq is required but not installed"
        exit 1
    fi
}

# Function to send notification
send_notification() {
    local title="$1"
    local message="$2"
    local status="$3"  # success/failure

    read_config

    local notify_on_success=$(jq -r '.backup_config.notifications.notify_on_success' "${CONFIG_FILE}")
    local notify_on_failure=$(jq -r '.backup_config.notifications.notify_on_failure' "${CONFIG_FILE}")

    # Check if we should send notification
    if [[ "$status" == "success" && "$notify_on_success" != "true" ]]; then
        return 0
    fi
    if [[ "$status" == "failure" && "$notify_on_failure" != "true" ]]; then
        return 0
    fi

    # Slack notification
    local slack_webhook=$(jq -r '.backup_config.notifications.slack_webhook' "${CONFIG_FILE}")
    if [[ -n "$slack_webhook" && "$slack_webhook" != "null" ]]; then
        local color="good"
        if [[ "$status" == "failure" ]]; then
            color="danger"
        fi

        local payload=$(cat << EOF
{
    "attachments": [
        {
            "color": "${color}",
            "title": "Resee Backup: ${title}",
            "text": "${message}",
            "ts": $(date +%s)
        }
    ]
}
EOF
)

        if curl -X POST -H 'Content-type: application/json' --data "${payload}" "${slack_webhook}" >/dev/null 2>&1; then
            log "INFO" "Slack notification sent"
        else
            log "WARN" "Failed to send Slack notification"
        fi
    fi

    # Email notification (if configured with sendmail or similar)
    local email_recipients=$(jq -r '.backup_config.notifications.email_recipients[]' "${CONFIG_FILE}" 2>/dev/null)
    if [[ -n "$email_recipients" ]] && command -v sendmail >/dev/null 2>&1; then
        echo "$email_recipients" | while read -r email; do
            if [[ -n "$email" ]]; then
                (
                    echo "Subject: Resee Backup: ${title}"
                    echo "To: ${email}"
                    echo ""
                    echo "${message}"
                ) | sendmail "${email}"
                log "INFO" "Email notification sent to ${email}"
            fi
        done
    fi
}

# Function to perform database backup
backup_database() {
    log "INFO" "Starting database backup..."

    if [[ ! -x "${SCRIPT_DIR}/backup_database.sh" ]]; then
        log "ERROR" "Database backup script not found or not executable"
        return 1
    fi

    if "${SCRIPT_DIR}/backup_database.sh"; then
        log "INFO" "Database backup completed successfully"
        return 0
    else
        log "ERROR" "Database backup failed"
        return 1
    fi
}

# Function to perform user data backup
backup_user_data() {
    log "INFO" "Starting user data backup..."

    read_config
    local compress_flag=""
    local compress_enabled=$(jq -r '.backup_config.user_data.compress' "${CONFIG_FILE}")
    if [[ "$compress_enabled" != "true" ]]; then
        compress_flag="--no-compress"
    fi

    # Check if we're running inside Docker container
    if [[ -f "/app/manage.py" ]]; then
        # Running inside container
        python "${SCRIPT_DIR}/backup_user_data.py" ${compress_flag} --backup-dir "${USER_DATA_BACKUP_DIR}"
    else
        # Running on host, use Docker
        if docker exec resee-project-backend-1 python /app/scripts/backup_user_data.py ${compress_flag} --backup-dir "${USER_DATA_BACKUP_DIR}"; then
            log "INFO" "User data backup completed successfully"
            return 0
        else
            log "ERROR" "User data backup failed"
            return 1
        fi
    fi
}

# Function to verify backup integrity
verify_backup_integrity() {
    local backup_type="$1"
    local backup_file="$2"

    log "INFO" "Verifying ${backup_type} backup integrity..."

    case "$backup_type" in
        "database")
            if [[ "$backup_file" == *.gz ]]; then
                if gunzip -t "${backup_file}" 2>/dev/null; then
                    log "INFO" "Database backup integrity verified"
                    return 0
                else
                    log "ERROR" "Database backup integrity check failed"
                    return 1
                fi
            fi
            ;;
        "user_data")
            if [[ "$backup_file" == *.gz ]]; then
                if gunzip -t "${backup_file}" && gunzip -c "${backup_file}" | jq . >/dev/null 2>&1; then
                    log "INFO" "User data backup integrity verified"
                    return 0
                else
                    log "ERROR" "User data backup integrity check failed"
                    return 1
                fi
            elif [[ "$backup_file" == *.json ]]; then
                if jq . "${backup_file}" >/dev/null 2>&1; then
                    log "INFO" "User data backup integrity verified"
                    return 0
                else
                    log "ERROR" "User data backup integrity check failed"
                    return 1
                fi
            fi
            ;;
    esac

    log "WARN" "Unknown backup type for integrity check: ${backup_type}"
    return 1
}

# Function to check backup health
check_backup_health() {
    read_config

    local max_age_hours=$(jq -r '.backup_config.health_checks.max_backup_age_hours' "${CONFIG_FILE}")
    local verify_integrity=$(jq -r '.backup_config.health_checks.verify_integrity' "${CONFIG_FILE}")
    local current_time=$(date +%s)
    local cutoff_time=$((current_time - max_age_hours * 3600))

    log "INFO" "Checking backup health..."

    # Check database backups
    local latest_db_backup=$(find "${DB_BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_db_backup" ]]; then
        local backup_time=$(stat -c %Y "${latest_db_backup}")
        if [[ $backup_time -lt $cutoff_time ]]; then
            log "WARN" "Latest database backup is older than ${max_age_hours} hours"
            return 1
        fi

        if [[ "$verify_integrity" == "true" ]]; then
            verify_backup_integrity "database" "${latest_db_backup}"
        fi
    else
        log "WARN" "No database backups found"
        return 1
    fi

    # Check user data backups
    local latest_user_backup=$(find "${USER_DATA_BACKUP_DIR}" -name "user_data_backup_*.json*" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_user_backup" ]]; then
        local backup_time=$(stat -c %Y "${latest_user_backup}")
        if [[ $backup_time -lt $cutoff_time ]]; then
            log "WARN" "Latest user data backup is older than ${max_age_hours} hours"
            return 1
        fi

        if [[ "$verify_integrity" == "true" ]]; then
            verify_backup_integrity "user_data" "${latest_user_backup}"
        fi
    else
        log "WARN" "No user data backups found"
        return 1
    fi

    log "INFO" "Backup health check passed"
    return 0
}

# Function to run full backup
run_full_backup() {
    local backup_type="${1:-daily}"

    log "INFO" "Starting ${backup_type} backup process..."

    local db_success=false
    local user_data_success=false
    local overall_success=true

    read_config

    # Database backup
    if [[ "$(jq -r '.backup_config.database.enabled' "${CONFIG_FILE}")" == "true" ]]; then
        if backup_database; then
            db_success=true
        else
            overall_success=false
        fi
    else
        log "INFO" "Database backup disabled in configuration"
        db_success=true
    fi

    # User data backup
    if [[ "$(jq -r '.backup_config.user_data.enabled' "${CONFIG_FILE}")" == "true" ]]; then
        if backup_user_data; then
            user_data_success=true
        else
            overall_success=false
        fi
    else
        log "INFO" "User data backup disabled in configuration"
        user_data_success=true
    fi

    # Health check
    if [[ "$overall_success" == "true" ]]; then
        check_backup_health
        overall_success=$?
    fi

    # Send notification
    if [[ "$overall_success" == "true" ]]; then
        local message="✅ ${backup_type} backup completed successfully\n\n"
        message+="Database backup: $([ "$db_success" == "true" ] && echo "✅ Success" || echo "❌ Failed")\n"
        message+="User data backup: $([ "$user_data_success" == "true" ] && echo "✅ Success" || echo "❌ Failed")"

        send_notification "${backup_type} Backup Successful" "$message" "success"
        log "INFO" "${backup_type} backup process completed successfully"
    else
        local message="❌ ${backup_type} backup failed\n\n"
        message+="Database backup: $([ "$db_success" == "true" ] && echo "✅ Success" || echo "❌ Failed")\n"
        message+="User data backup: $([ "$user_data_success" == "true" ] && echo "✅ Success" || echo "❌ Failed")\n\n"
        message+="Check logs: ${LOGS_DIR}/backup_manager.log"

        send_notification "${backup_type} Backup Failed" "$message" "failure"
        log "ERROR" "${backup_type} backup process failed"
    fi

    return $([[ "$overall_success" == "true" ]] && echo 0 || echo 1)
}

# Function to show status
show_status() {
    echo "=== RESEE BACKUP STATUS ==="
    echo

    # Configuration status
    if [[ -f "${CONFIG_FILE}" ]]; then
        echo "✅ Configuration: Found"
        read_config
        echo "  - Database backups: $(jq -r '.backup_config.database.enabled' "${CONFIG_FILE}")"
        echo "  - User data backups: $(jq -r '.backup_config.user_data.enabled' "${CONFIG_FILE}")"
    else
        echo "❌ Configuration: Missing"
    fi
    echo

    # Latest backups
    echo "📊 Latest Backups:"
    local latest_db_backup=$(find "${DB_BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_db_backup" ]]; then
        echo "  - Database: $(basename "$latest_db_backup") ($(date -r "$latest_db_backup"))"
    else
        echo "  - Database: No backups found"
    fi

    local latest_user_backup=$(find "${USER_DATA_BACKUP_DIR}" -name "user_data_backup_*.json*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_user_backup" ]]; then
        echo "  - User Data: $(basename "$latest_user_backup") ($(date -r "$latest_user_backup"))"
    else
        echo "  - User Data: No backups found"
    fi
    echo

    # Backup counts
    echo "📈 Backup Counts:"
    echo "  - Database backups: $(find "${DB_BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f | wc -l)"
    echo "  - User data backups: $(find "${USER_DATA_BACKUP_DIR}" -name "user_data_backup_*.json*" -type f | wc -l)"
    echo

    # Disk usage
    echo "💾 Disk Usage:"
    if [[ -d "${DB_BACKUP_DIR}" ]]; then
        echo "  - Database backups: $(du -sh "${DB_BACKUP_DIR}" 2>/dev/null | cut -f1)"
    fi
    if [[ -d "${USER_DATA_BACKUP_DIR}" ]]; then
        echo "  - User data backups: $(du -sh "${USER_DATA_BACKUP_DIR}" 2>/dev/null | cut -f1)"
    fi
    echo "  - Total backup storage: $(du -sh "${BACKUP_ROOT}" 2>/dev/null | cut -f1)"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
  backup [type]     Run backup (type: daily, weekly, monthly)
  status           Show backup status and statistics
  health           Run health check only
  config           Show/edit configuration
  cleanup          Clean up old backups
  restore          Interactive restore assistant

Examples:
  $0 backup daily          # Run daily backup
  $0 backup               # Run daily backup (default)
  $0 status               # Show status
  $0 health               # Check backup health
  $0 cleanup              # Clean up old backups

EOF
}

# Main execution
main() {
    local command="${1:-}"

    case "$command" in
        backup)
            local backup_type="${2:-daily}"
            run_full_backup "$backup_type"
            ;;
        status)
            show_status
            ;;
        health)
            check_backup_health
            ;;
        config)
            read_config
            echo "Configuration file: ${CONFIG_FILE}"
            if command -v jq >/dev/null 2>&1; then
                jq . "${CONFIG_FILE}"
            else
                cat "${CONFIG_FILE}"
            fi
            ;;
        cleanup)
            log "INFO" "Starting cleanup of old backups..."
            "${SCRIPT_DIR}/backup_database.sh" 2>/dev/null || true
            python "${SCRIPT_DIR}/backup_user_data.py" --retention-days 30 2>/dev/null || true
            log "INFO" "Cleanup completed"
            ;;
        restore)
            echo "🔄 Restore Assistant"
            echo "Available database backups:"
            find "${DB_BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f -printf '%TY-%Tm-%Td %TH:%TM  %f\n' | sort -r | head -10
            echo
            read -p "Enter backup filename to restore: " backup_file
            if [[ -n "$backup_file" ]]; then
                "${SCRIPT_DIR}/restore_database.sh" "$backup_file"
            fi
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Error handling
trap 'log "ERROR" "Backup manager script failed at line $LINENO"' ERR

# Run main function
main "$@"