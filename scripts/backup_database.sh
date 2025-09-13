#!/bin/bash

# Simple Database Backup Script for Resee Project
# Creates PostgreSQL backup with basic rotation

set -euo pipefail

# Configuration
CONTAINER_NAME="resee-project-db-1"
DB_NAME="resee_db"
DB_USER="resee_user"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="resee_db_backup_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    log "ERROR: Container ${CONTAINER_NAME} is not running"
    exit 1
fi

log "Starting database backup..."

# Create backup
if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"; then
    log "SUCCESS: Database backup created - ${BACKUP_FILE}"
    log "Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"
else
    log "ERROR: Database backup failed"
    exit 1
fi

# Simple cleanup - keep only last 7 backups
log "Cleaning up old backups (keeping last 7)..."
cd "$BACKUP_DIR"
ls -t resee_db_backup_*.sql.gz | tail -n +8 | xargs rm -f 2>/dev/null || true

log "Backup completed successfully"