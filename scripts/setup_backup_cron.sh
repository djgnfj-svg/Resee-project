#!/bin/bash

# Simple Backup Cron Setup for Resee Project
# Sets up daily automated backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup_database.sh"
LOG_FILE="${SCRIPT_DIR}/../backups/backup.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if backup script exists
if [[ ! -f "$BACKUP_SCRIPT" ]]; then
    log "ERROR: Backup script not found at $BACKUP_SCRIPT"
    exit 1
fi

# Make sure backup script is executable
chmod +x "$BACKUP_SCRIPT"

# Create backup directory and log file
mkdir -p "${SCRIPT_DIR}/../backups"
touch "$LOG_FILE"

log "Setting up daily backup automation..."

# Create cron entry
CRON_ENTRY="0 2 * * * cd ${SCRIPT_DIR}/.. && ./scripts/backup_database.sh >> backups/backup.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "backup_database.sh"; then
    log "Backup cron job already exists"
    log "Current backup-related cron jobs:"
    crontab -l 2>/dev/null | grep "backup_database.sh" || true
else
    # Add new cron entry
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    log "SUCCESS: Daily backup scheduled at 2:00 AM"
    log "Cron entry: $CRON_ENTRY"
fi

# Show current cron jobs
log "Current cron jobs:"
crontab -l 2>/dev/null || log "No cron jobs found"

log "Setup completed successfully!"
log "Backup logs will be saved to: $LOG_FILE"
log "To manually run backup: $BACKUP_SCRIPT"
log "To remove cron job: crontab -e (remove the backup_database.sh line)"