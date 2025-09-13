#!/bin/bash

# Setup automated backup schedule using cron
# This script configures daily, weekly, and monthly backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_MANAGER="${SCRIPT_DIR}/backup_manager.sh"
CRON_FILE="/tmp/resee_backup_cron"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if backup manager exists
if [[ ! -f "$BACKUP_MANAGER" ]]; then
    log "ERROR: Backup manager not found at $BACKUP_MANAGER"
    exit 1
fi

# Make sure backup manager is executable
chmod +x "$BACKUP_MANAGER"

log "Setting up automated backup schedule..."

# Create cron configuration
cat > "$CRON_FILE" << EOF
# Resee Project Automated Backup Schedule
# Generated on $(date)

# Daily backup at 2:00 AM
0 2 * * * $BACKUP_MANAGER backup daily >> /backups/logs/daily_backup.log 2>&1

# Weekly backup on Sunday at 3:00 AM
0 3 * * 0 $BACKUP_MANAGER backup weekly >> /backups/logs/weekly_backup.log 2>&1

# Monthly backup on 1st day at 4:00 AM
0 4 1 * * $BACKUP_MANAGER backup monthly >> /backups/logs/monthly_backup.log 2>&1

# Health check every 6 hours
0 */6 * * * $BACKUP_MANAGER health >> /backups/logs/health_check.log 2>&1

# Cleanup old backups weekly on Saturday at 1:00 AM
0 1 * * 6 $BACKUP_MANAGER cleanup >> /backups/logs/cleanup.log 2>&1

EOF

# Display the cron configuration
log "Proposed cron configuration:"
cat "$CRON_FILE"
echo

# Function to install cron
install_cron() {
    # Check if running as root or if sudo is available
    if [[ $EUID -eq 0 ]]; then
        # Running as root
        crontab "$CRON_FILE"
        log "SUCCESS: Cron jobs installed as root"
    elif command -v sudo >/dev/null 2>&1; then
        # Use sudo
        sudo crontab "$CRON_FILE"
        log "SUCCESS: Cron jobs installed using sudo"
    else
        # Regular user installation
        crontab "$CRON_FILE"
        log "SUCCESS: Cron jobs installed for current user"
    fi
}

# Function to create systemd timer (alternative to cron)
create_systemd_timer() {
    local service_dir="/etc/systemd/system"
    local user_service_dir="$HOME/.config/systemd/user"

    # Choose directory based on privileges
    if [[ $EUID -eq 0 ]]; then
        local target_dir="$service_dir"
    else
        mkdir -p "$user_service_dir"
        local target_dir="$user_service_dir"
    fi

    # Create service file
    cat > "$target_dir/resee-backup.service" << EOF
[Unit]
Description=Resee Database Backup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=$BACKUP_MANAGER backup daily
User=$(whoami)
StandardOutput=append:/backups/logs/systemd_backup.log
StandardError=append:/backups/logs/systemd_backup.log

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file
    cat > "$target_dir/resee-backup.timer" << EOF
[Unit]
Description=Run Resee backup daily
Requires=resee-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start timer
    if [[ $EUID -eq 0 ]]; then
        systemctl daemon-reload
        systemctl enable resee-backup.timer
        systemctl start resee-backup.timer
        log "SUCCESS: Systemd timer installed and started"
    else
        systemctl --user daemon-reload
        systemctl --user enable resee-backup.timer
        systemctl --user start resee-backup.timer
        log "SUCCESS: User systemd timer installed and started"
    fi
}

# Function to show current cron jobs
show_current_cron() {
    log "Current cron jobs:"
    if crontab -l 2>/dev/null; then
        echo
    else
        log "No current cron jobs found"
    fi
}

# Interactive setup
interactive_setup() {
    echo
    log "=== Resee Backup Schedule Setup ==="
    echo

    show_current_cron

    echo
    echo "Setup options:"
    echo "1. Install cron jobs (recommended)"
    echo "2. Create systemd timer"
    echo "3. Show configuration only"
    echo "4. Exit"
    echo

    read -p "Choose option [1-4]: " choice

    case $choice in
        1)
            read -p "This will replace existing cron jobs. Continue? [y/N]: " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                install_cron
                log "Backup schedule installed successfully!"
                echo
                echo "Backup schedule:"
                echo "- Daily backup: 2:00 AM"
                echo "- Weekly backup: Sunday 3:00 AM"
                echo "- Monthly backup: 1st day 4:00 AM"
                echo "- Health check: Every 6 hours"
                echo "- Cleanup: Saturday 1:00 AM"
                echo
                echo "To manually run a backup: $BACKUP_MANAGER backup"
                echo "To check status: $BACKUP_MANAGER status"
            else
                log "Installation cancelled"
            fi
            ;;
        2)
            if command -v systemctl >/dev/null 2>&1; then
                create_systemd_timer
            else
                log "ERROR: systemd not available on this system"
                exit 1
            fi
            ;;
        3)
            log "Configuration saved to: $CRON_FILE"
            log "To install manually: crontab $CRON_FILE"
            ;;
        4)
            log "Setup cancelled"
            exit 0
            ;;
        *)
            log "Invalid option"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    local command="${1:-interactive}"

    case $command in
        interactive)
            interactive_setup
            ;;
        install)
            install_cron
            ;;
        systemd)
            create_systemd_timer
            ;;
        show)
            show_current_cron
            ;;
        *)
            echo "Usage: $0 [interactive|install|systemd|show]"
            echo "  interactive  - Interactive setup (default)"
            echo "  install      - Install cron jobs directly"
            echo "  systemd      - Create systemd timer"
            echo "  show         - Show current cron jobs"
            exit 1
            ;;
    esac
}

# Cleanup temporary file on exit
trap 'rm -f "$CRON_FILE"' EXIT

# Run main function
main "$@"