#!/bin/bash

# PostgreSQL Backup Script for Resee
# Usage: bash scripts/backup_db.sh

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="resee_backup_${TIMESTAMP}.sql.gz"
DB_NAME="${DB_NAME:-resee_dev}"
DB_USER="${DB_USER:-postgres}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup: $BACKUP_FILE"

# Perform backup via docker-compose
docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"

    # Remove old backups (older than RETENTION_DAYS)
    find "$BACKUP_DIR" -name "resee_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned (retention: ${RETENTION_DAYS} days)"
else
    echo "Backup failed"
    exit 1
fi
