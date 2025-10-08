#!/bin/bash

# PostgreSQL Restore Script for Resee
# Usage: bash scripts/restore_db.sh [backup_file]

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${DB_NAME:-resee_dev}"
DB_USER="${DB_USER:-postgres}"

# List available backups if no file specified
if [ -z "$1" ]; then
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | awk '{print $9, "(" $5 ")"}'
    echo ""
    echo "Usage: bash scripts/restore_db.sh <backup_file>"
    exit 0
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm restore
echo "WARNING: This will replace all data in database '$DB_NAME'"
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Perform restore via docker-compose
echo "Restoring database..."
gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME"

if [ $? -eq 0 ]; then
    echo "Restore completed successfully"
else
    echo "Restore failed"
    exit 1
fi
