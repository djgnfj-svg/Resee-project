#!/bin/bash

# Database Backup Script for Resee Project
# This script creates compressed PostgreSQL backups with rotation

set -euo pipefail

# Configuration
CONTAINER_NAME="resee-project-db-1"
DB_NAME="resee_db"
DB_USER="resee_user"
BACKUP_DIR="/backups/postgresql"
BACKUP_RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="resee_db_backup_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/backup.log"
}

# Function to check if container is running
check_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log "ERROR: Container ${CONTAINER_NAME} is not running"
        exit 1
    fi
}

# Function to create backup
create_backup() {
    log "Starting database backup..."

    # Create compressed backup
    if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"; then
        log "SUCCESS: Backup created - ${BACKUP_FILE}"

        # Verify backup file exists and is not empty
        if [[ -s "${BACKUP_DIR}/${BACKUP_FILE}" ]]; then
            log "INFO: Backup file size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"
        else
            log "ERROR: Backup file is empty or doesn't exist"
            exit 1
        fi
    else
        log "ERROR: Failed to create backup"
        exit 1
    fi
}

# Function to rotate old backups
rotate_backups() {
    log "Rotating old backups (keeping last ${BACKUP_RETENTION_DAYS} days)..."

    # Find and delete backups older than retention period
    if find "${BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete 2>/dev/null; then
        log "INFO: Old backups cleaned up"
    else
        log "INFO: No old backups to clean up"
    fi

    # Log current backup count
    BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "resee_db_backup_*.sql.gz" -type f | wc -l)
    log "INFO: Current backup count: ${BACKUP_COUNT}"
}

# Function to test backup integrity
test_backup() {
    log "Testing backup integrity..."

    if gunzip -t "${BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null; then
        log "SUCCESS: Backup integrity verified"
    else
        log "ERROR: Backup file is corrupted"
        exit 1
    fi
}

# Function to create backup metadata
create_metadata() {
    local metadata_file="${BACKUP_DIR}/${BACKUP_FILE}.meta"

    cat > "${metadata_file}" << EOF
{
    "backup_timestamp": "$(date -Iseconds)",
    "database_name": "${DB_NAME}",
    "database_user": "${DB_USER}",
    "container_name": "${CONTAINER_NAME}",
    "backup_file": "${BACKUP_FILE}",
    "backup_size_bytes": $(stat -c%s "${BACKUP_DIR}/${BACKUP_FILE}"),
    "backup_size_human": "$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)",
    "retention_days": ${BACKUP_RETENTION_DAYS}
}
EOF

    log "INFO: Metadata created - ${BACKUP_FILE}.meta"
}

# Main execution
main() {
    log "=== DATABASE BACKUP START ==="

    # Pre-flight checks
    check_container

    # Create backup
    create_backup

    # Test backup integrity
    test_backup

    # Create metadata
    create_metadata

    # Rotate old backups
    rotate_backups

    log "=== DATABASE BACKUP COMPLETE ==="
    log "Backup location: ${BACKUP_DIR}/${BACKUP_FILE}"
}

# Error handling
trap 'log "ERROR: Backup script failed at line $LINENO"' ERR

# Run main function
main "$@"