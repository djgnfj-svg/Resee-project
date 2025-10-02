#!/bin/bash

# Health Monitor Script for Resee Application
# Monitors the health endpoint and restarts services if unhealthy

# Configuration
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/api/health/}"
MAX_FAILURES=3
FAILURE_COUNT_FILE="/tmp/resee_health_failures.txt"
LOG_FILE="/var/log/resee/health_monitor.log"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Initialize failure count file if it doesn't exist
if [ ! -f "$FAILURE_COUNT_FILE" ]; then
    echo "0" > "$FAILURE_COUNT_FILE"
fi

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to get current failure count
get_failure_count() {
    cat "$FAILURE_COUNT_FILE"
}

# Function to increment failure count
increment_failure_count() {
    local count=$(get_failure_count)
    echo $((count + 1)) > "$FAILURE_COUNT_FILE"
}

# Function to reset failure count
reset_failure_count() {
    echo "0" > "$FAILURE_COUNT_FILE"
}

# Function to restart backend service
restart_backend() {
    log_message "WARNING: Restarting backend service due to health check failures"

    # Restart backend using docker-compose
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart backend

    if [ $? -eq 0 ]; then
        log_message "SUCCESS: Backend service restarted successfully"
        reset_failure_count
        return 0
    else
        log_message "ERROR: Failed to restart backend service"
        return 1
    fi
}

# Main health check logic
log_message "INFO: Starting health check"

# Perform health check using curl
response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$HEALTH_URL")

if [ "$response" = "200" ]; then
    log_message "SUCCESS: Health check passed (HTTP $response)"
    reset_failure_count
    exit 0
else
    log_message "ERROR: Health check failed (HTTP $response)"
    increment_failure_count

    current_failures=$(get_failure_count)
    log_message "WARNING: Consecutive failures: $current_failures/$MAX_FAILURES"

    if [ "$current_failures" -ge "$MAX_FAILURES" ]; then
        log_message "CRITICAL: Max failures reached, initiating restart"
        restart_backend
        exit 1
    fi

    exit 1
fi
