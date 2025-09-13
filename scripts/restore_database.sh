#!/bin/bash

# Database Restore Script for Resee Project
# This script restores PostgreSQL backups with safety checks

set -euo pipefail

# Configuration
CONTAINER_NAME="resee-project-db-1"
DB_NAME="resee_db"
DB_USER="resee_user"
BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 <backup_file>

Examples:
  $0 resee_db_backup_20250913_120000.sql.gz
  $0 /path/to/custom/backup.sql.gz

Options:
  -h, --help          Show this help message
  -f, --force         Skip confirmation prompts (DANGEROUS)
  --dry-run           Show what would be restored without actually doing it

Environment Variables:
  CONTAINER_NAME      Docker container name (default: resee-project-db-1)
  DB_NAME            Database name (default: resee_db)
  DB_USER            Database user (default: resee_user)
EOF
}

# Parse command line arguments
BACKUP_FILE=""
FORCE_MODE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--force)
            FORCE_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            log "ERROR: Unknown option $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$BACKUP_FILE" ]]; then
                BACKUP_FILE="$1"
            else
                log "ERROR: Multiple backup files specified"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$BACKUP_FILE" ]]; then
    log "ERROR: No backup file specified"
    usage
    exit 1
fi

# Function to check if container is running
check_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log "ERROR: Container ${CONTAINER_NAME} is not running"
        exit 1
    fi
}

# Function to validate backup file
validate_backup() {
    local backup_path="$1"

    # Check if file exists
    if [[ ! -f "$backup_path" ]]; then
        log "ERROR: Backup file does not exist: $backup_path"
        exit 1
    fi

    # Check if file is readable
    if [[ ! -r "$backup_path" ]]; then
        log "ERROR: Cannot read backup file: $backup_path"
        exit 1
    fi

    # Check if gzipped file is valid
    if [[ "$backup_path" == *.gz ]]; then
        if ! gunzip -t "$backup_path" 2>/dev/null; then
            log "ERROR: Backup file is corrupted or not a valid gzip file: $backup_path"
            exit 1
        fi
    fi

    log "SUCCESS: Backup file validation passed"
}

# Function to get backup file path
get_backup_path() {
    local file="$1"

    # If absolute path is provided, use it directly
    if [[ "$file" == /* ]]; then
        echo "$file"
        return
    fi

    # If only filename is provided, look in backup directory
    if [[ -f "${BACKUP_DIR}/$file" ]]; then
        echo "${BACKUP_DIR}/$file"
        return
    fi

    # File not found in backup directory, use as-is (will fail validation)
    echo "$file"
}

# Function to create pre-restore backup
create_pre_restore_backup() {
    log "Creating pre-restore backup for safety..."

    local pre_restore_backup="resee_db_pre_restore_${TIMESTAMP}.sql.gz"
    local backup_path="${BACKUP_DIR}/${pre_restore_backup}"

    if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "$backup_path"; then
        log "SUCCESS: Pre-restore backup created - $pre_restore_backup"
        echo "$backup_path"
    else
        log "ERROR: Failed to create pre-restore backup"
        exit 1
    fi
}

# Function to get database info
get_database_info() {
    log "Current database information:"

    # Get table count
    local table_count
    table_count=$(docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    log "  - Tables: $table_count"

    # Get approximate row counts for main tables
    local tables=("accounts_user" "content_content" "review_reviewschedule" "review_reviewhistory")
    for table in "${tables[@]}"; do
        local count
        if count=$(docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' '); then
            log "  - $table: $count rows"
        else
            log "  - $table: table not found or error"
        fi
    done
}

# Function to show backup info
show_backup_info() {
    local backup_path="$1"

    log "Backup file information:"
    log "  - File: $backup_path"
    log "  - Size: $(du -h "$backup_path" | cut -f1)"
    log "  - Modified: $(date -r "$backup_path")"

    # Check for metadata file
    local meta_file="${backup_path}.meta"
    if [[ -f "$meta_file" ]]; then
        log "  - Metadata available: $meta_file"
        if command -v jq >/dev/null 2>&1; then
            local backup_timestamp
            backup_timestamp=$(jq -r '.backup_timestamp' "$meta_file" 2>/dev/null || echo "unknown")
            log "  - Backup timestamp: $backup_timestamp"
        fi
    fi
}

# Function to confirm restore
confirm_restore() {
    if [[ "$FORCE_MODE" == true ]]; then
        log "WARNING: Force mode enabled - skipping confirmation"
        return
    fi

    echo
    log "WARNING: This will completely replace the current database!"
    log "All current data will be lost unless you have a backup."
    echo
    read -p "Are you sure you want to proceed? Type 'YES' to continue: " -r
    echo

    if [[ $REPLY != "YES" ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
}

# Function to restore database
restore_database() {
    local backup_path="$1"

    log "Starting database restore..."

    # Drop existing connections
    log "Terminating existing database connections..."
    if docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid != pg_backend_pid();" >/dev/null 2>&1; then
        log "SUCCESS: Existing connections terminated"
    else
        log "WARNING: Could not terminate some connections"
    fi

    # Drop and recreate database
    log "Dropping and recreating database..."
    if docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" &&
       docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"; then
        log "SUCCESS: Database recreated"
    else
        log "ERROR: Failed to recreate database"
        exit 1
    fi

    # Restore from backup
    log "Restoring data from backup..."
    if [[ "$backup_path" == *.gz ]]; then
        if gunzip -c "$backup_path" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"; then
            log "SUCCESS: Database restored from compressed backup"
        else
            log "ERROR: Failed to restore from compressed backup"
            exit 1
        fi
    else
        if docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "$backup_path"; then
            log "SUCCESS: Database restored from uncompressed backup"
        else
            log "ERROR: Failed to restore from uncompressed backup"
            exit 1
        fi
    fi
}

# Function to verify restore
verify_restore() {
    log "Verifying restored database..."

    # Check if we can connect
    if docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" >/dev/null 2>&1; then
        log "SUCCESS: Database connection verified"
    else
        log "ERROR: Cannot connect to restored database"
        exit 1
    fi

    # Show new database info
    get_database_info
}

# Main execution
main() {
    log "=== DATABASE RESTORE START ==="

    # Parse backup file path
    local backup_path
    backup_path=$(get_backup_path "$BACKUP_FILE")

    # Pre-flight checks
    check_container
    validate_backup "$backup_path"

    # Show current database info
    get_database_info

    # Show backup info
    show_backup_info "$backup_path"

    if [[ "$DRY_RUN" == true ]]; then
        log "DRY RUN: Would restore from $backup_path"
        log "DRY RUN: No changes made"
        exit 0
    fi

    # Confirm restore
    confirm_restore

    # Create safety backup
    local pre_restore_backup
    pre_restore_backup=$(create_pre_restore_backup)

    # Perform restore
    restore_database "$backup_path"

    # Verify restore
    verify_restore

    log "=== DATABASE RESTORE COMPLETE ==="
    log "Pre-restore backup saved: $pre_restore_backup"
}

# Error handling
trap 'log "ERROR: Restore script failed at line $LINENO"' ERR

# Run main function
main "$@"