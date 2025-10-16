#!/bin/bash

# PostgreSQL Backup Script for Resee
# Usage: bash scripts/backup_db.sh [production|development]
# Example: bash scripts/backup_db.sh production

# Function to send Slack alerts
send_slack_alert() {
    local message="$1"
    local level="${2:-error}"

    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local emoji="🔴"
        [ "$level" == "success" ] && emoji="✅"

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"${emoji} Database Backup Alert\",
                \"blocks\": [{
                    \"type\": \"section\",
                    \"text\": {
                        \"type\": \"mrkdwn\",
                        \"text\": \"$message\"
                    }
                }]
            }" \
            --silent --output /dev/null
    fi
}

# Configuration
ENVIRONMENT="${1:-development}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS=30  # 30일 보관
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="resee_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"

# Database configuration based on environment
if [ "$ENVIRONMENT" == "production" ]; then
    DB_NAME="${DB_NAME:-resee_prod}"
else
    DB_NAME="${DB_NAME:-resee_dev}"
fi
DB_USER="${DB_USER:-postgres}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup: $BACKUP_FILE (Environment: $ENVIRONMENT)"

# Perform backup via docker-compose
docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completed: $BACKUP_DIR/$BACKUP_FILE (Size: $BACKUP_SIZE)"

    # Verify backup integrity
    if gzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup integrity verified"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Backup integrity check failed!"
        send_slack_alert "Backup integrity check failed for $BACKUP_FILE"
        exit 1
    fi

    # Upload to S3 (if configured)
    if [ -n "$AWS_S3_BUCKET" ] && command -v aws &> /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Uploading to S3..."
        aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$AWS_S3_BUCKET/backups/database/" --storage-class STANDARD_IA
        if [ $? -eq 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] S3 upload completed"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: S3 upload failed"
            send_slack_alert "S3 upload failed for $BACKUP_FILE"
        fi
    fi

    # Remove old backups (older than RETENTION_DAYS)
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "resee_${ENVIRONMENT}_*.sql.gz" -type f -mtime +$RETENTION_DAYS)
    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | xargs rm -f
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Old backups cleaned (retention: ${RETENTION_DAYS} days)"
    fi

    # Send success notification
    send_slack_alert "✅ Database backup completed successfully\nFile: $BACKUP_FILE\nSize: $BACKUP_SIZE\nEnvironment: $ENVIRONMENT" "success"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Backup failed"
    send_slack_alert "❌ Database backup FAILED for $ENVIRONMENT environment"
    exit 1
fi
