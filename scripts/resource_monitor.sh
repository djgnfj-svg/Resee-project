#!/bin/bash

# Resource Monitor Script for Resee Application
# Monitors disk space and basic memory usage

# Configuration
DISK_WARNING_THRESHOLD=80
DISK_CRITICAL_THRESHOLD=90
MEMORY_WARNING_THRESHOLD=85
LOG_FILE="/var/log/resee/resource_monitor.log"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check disk space
check_disk_space() {
    log_message "INFO: Checking disk space"

    # Get disk usage percentage (excluding the % symbol)
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    log_message "INFO: Disk usage: ${disk_usage}%"

    if [ "$disk_usage" -ge "$DISK_CRITICAL_THRESHOLD" ]; then
        log_message "CRITICAL: Disk usage is at ${disk_usage}% (threshold: ${DISK_CRITICAL_THRESHOLD}%)"
        return 2
    elif [ "$disk_usage" -ge "$DISK_WARNING_THRESHOLD" ]; then
        log_message "WARNING: Disk usage is at ${disk_usage}% (threshold: ${DISK_WARNING_THRESHOLD}%)"
        return 1
    else
        log_message "SUCCESS: Disk usage is healthy"
        return 0
    fi
}

# Function to check memory usage
check_memory_usage() {
    log_message "INFO: Checking memory usage"

    # Get memory usage percentage
    memory_usage=$(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')

    log_message "INFO: Memory usage: ${memory_usage}%"

    if [ "$memory_usage" -ge "$MEMORY_WARNING_THRESHOLD" ]; then
        log_message "WARNING: Memory usage is at ${memory_usage}% (threshold: ${MEMORY_WARNING_THRESHOLD}%)"
        return 1
    else
        log_message "SUCCESS: Memory usage is healthy"
        return 0
    fi
}

# Function to check Docker containers status
check_docker_status() {
    log_message "INFO: Checking Docker containers status"

    # Get list of unhealthy or stopped containers
    unhealthy=$(docker ps -a --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null)
    stopped=$(docker ps -a --filter "status=exited" --filter "status=dead" --format "{{.Names}}" 2>/dev/null | grep -E "resee|backend|frontend|postgres|redis|celery")

    if [ -n "$unhealthy" ]; then
        log_message "WARNING: Unhealthy containers found: $unhealthy"
    fi

    if [ -n "$stopped" ]; then
        log_message "WARNING: Stopped containers found: $stopped"
    fi

    if [ -z "$unhealthy" ] && [ -z "$stopped" ]; then
        log_message "SUCCESS: All containers are healthy"
        return 0
    else
        return 1
    fi
}

# Function to display container resource usage
check_container_resources() {
    log_message "INFO: Container resource usage:"

    # Get container stats (single snapshot, no streaming)
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "resee|backend|frontend|postgres|redis|celery" | while read line; do
        log_message "INFO: $line"
    done
}

# Main monitoring logic
log_message "INFO: Starting resource monitoring"

# Perform checks
check_disk_space
disk_status=$?

check_memory_usage
memory_status=$?

check_docker_status
docker_status=$?

check_container_resources

# Summary
log_message "INFO: Resource monitoring completed"

# Exit with the highest severity status
if [ $disk_status -eq 2 ]; then
    exit 2
elif [ $disk_status -eq 1 ] || [ $memory_status -eq 1 ] || [ $docker_status -eq 1 ]; then
    exit 1
else
    exit 0
fi
