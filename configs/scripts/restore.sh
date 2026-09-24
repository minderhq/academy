#!/bin/bash
# PROJECT-OMEGA Restore Script
# Automated restore from backup

set -e

# ============================================
# Configuration
# ============================================
BACKUP_ROOT="/volume1/backup/project-omega"
DATA_ROOT="/volume1/docker/project-omega"
BACKUP_NAME=""

# Services to restore
RESTORE_QDRANT=true
RESTORE_NEO4J=true
RESTORE_REDIS=true
RESTORE_MONITORING=true

# Dry run (don't actually restore)
DRY_RUN=false

# Notification settings
SLACK_WEBHOOK=""
TELEGRAM_TOKEN=""
TELEGRAM_CHAT_ID=""

# ============================================
# Functions
# ============================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    log "ERROR: $1"
    notify "Restore failed: $1" "error"
    exit 1
}

notify() {
    local message="$1"
    local status="${2:-info}"

    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"[${status^^}] ${message}\"}" > /dev/null
    fi

    if [[ -n "$TELEGRAM_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
        curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${message}" > /dev/null
    fi
}

list_backups() {
    log "Available backups:"
    ls -lht "${BACKUP_ROOT}"/omega_backup_*.* 2>/dev/null || log "No backups found"
}

extract_backup() {
    local backup_file="$1"

    if [[ "$backup_file" == *.tar.gz ]]; then
        log "Extracting backup archive..."
        tar -xzf "${backup_file}" -C "${BACKUP_ROOT}"
        BACKUP_NAME=$(basename "${backup_file}" .tar.gz)
    elif [[ "$backup_file" == *.tar.gz.enc ]]; then
        log "Decrypting and extracting backup..."
        if [[ -z "${BACKUP_ENCRYPTION_KEY}" ]]; then
            error "Encryption key not set. Please set BACKUP_ENCRYPTION_KEY environment variable."
        fi
        openssl enc -d -aes-256-cbc -pbkdf2 \
            -in "${backup_file}" \
            -out "/tmp/backup_temp.tar.gz" \
            -k "${BACKUP_ENCRYPTION_KEY}"
        tar -xzf "/tmp/backup_temp.tar.gz" -C "${BACKUP_ROOT}"
        rm "/tmp/backup_temp.tar.gz"
        BACKUP_NAME=$(basename "${backup_file}" .tar.gz.enc)
    else
        BACKUP_NAME=$(basename "${backup_file}")
    fi

    log "Restoring from backup: ${BACKUP_NAME}"
}

stop_services() {
    log "Stopping services..."

    docker-compose -f "${DATA_ROOT}/docker-compose-complete.yml" stop

    # Wait for services to stop
    sleep 10
}

start_services() {
    log "Starting services..."

    docker-compose -f "${DATA_ROOT}/docker-compose-complete.yml" start

    # Wait for services to be ready
    sleep 30
}

restore_qdrant() {
    if [[ "$RESTORE_QDRANT" != true ]]; then
        return
    fi

    log "Restoring Qdrant data..."

    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would restore Qdrant data from ${BACKUP_DIR}/data/qdrant/"
        return
    fi

    if [[ -d "${BACKUP_DIR}/data/qdrant" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/qdrant/" "${DATA_ROOT}/data/qdrant/"
    fi
}

restore_neo4j() {
    if [[ "$RESTORE_NEO4J" != true ]]; then
        return
    fi

    log "Restoring Neo4j data..."

    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would restore Neo4j data from ${BACKUP_DIR}/data/neo4j/"
        return
    fi

    # Stop Neo4j first
    docker stop project-omega-neo4j 2>/dev/null || true

    if [[ -d "${BACKUP_DIR}/data/neo4j" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/neo4j/" "${DATA_ROOT}/data/neo4j/"
    fi

    # Restore from backup if available
    if [[ -f "${BACKUP_DIR}/database/neo4j.backup" ]]; then
        docker cp "${BACKUP_DIR}/database/neo4j.backup" project-omega-neo4j:/backups/
        docker exec project-omega-neo4j \
            neo4j-admin database load neo4j --from-path=/backups/ --force
    fi

    # Start Neo4j
    docker start project-omega-neo4j
}

restore_redis() {
    if [[ "$RESTORE_REDIS" != true ]]; then
        return
    fi

    log "Restoring Redis data..."

    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would restore Redis data from ${BACKUP_DIR}/data/redis/"
        return
    fi

    # Stop Redis first
    docker stop project-omega-redis 2>/dev/null || true

    if [[ -d "${BACKUP_DIR}/data/redis" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/redis/" "${DATA_ROOT}/data/redis/"
    fi

    # Restore RDB file if available
    if [[ -f "${BACKUP_DIR}/database/redis.rdb" ]]; then
        docker cp "${BACKUP_DIR}/database/redis.rdb" project-omega-redis:/tmp/dump.rdb
    fi

    # Start Redis
    docker start project-omega-redis
}

restore_monitoring() {
    if [[ "$RESTORE_MONITORING" != true ]]; then
        return
    fi

    log "Restoring monitoring data..."

    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would restore monitoring data from ${BACKUP_DIR}/data/"
        return
    fi

    # Prometheus
    if [[ -d "${BACKUP_DIR}/data/prometheus" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/prometheus/" "${DATA_ROOT}/data/prometheus/"
    fi

    # Grafana
    if [[ -d "${BACKUP_DIR}/data/grafana" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/grafana/" "${DATA_ROOT}/data/grafana/"
    fi

    # Loki
    if [[ -d "${BACKUP_DIR}/data/loki" ]]; then
        rsync -av --delete "${BACKUP_DIR}/data/loki/" "${DATA_ROOT}/data/loki/"
    fi
}

verify_restore() {
    log "Verifying restore..."

    # Check if services are running
    docker ps | grep -q project-omega-qdrant && log "✓ Qdrant is running" || log "✗ Qdrant is not running"
    docker ps | grep -q project-omega-neo4j && log "✓ Neo4j is running" || log "✗ Neo4j is not running"
    docker ps | grep -q project-omega-redis && log "✓ Redis is running" || log "✗ Redis is not running"

    # Check if data exists
    [[ -d "${DATA_ROOT}/data/qdrant" ]] && log "✓ Qdrant data exists" || log "✗ Qdrant data missing"
    [[ -d "${DATA_ROOT}/data/neo4j" ]] && log "✓ Neo4j data exists" || log "✗ Neo4j data missing"
    [[ -d "${DATA_ROOT}/data/redis" ]] && log "✓ Redis data exists" || log "✗ Redis data missing"
}

# ============================================
# Parse Arguments
# ============================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backup)
            BACKUP_NAME="$2"
            shift 2
            ;;
        -l|--list)
            list_backups
            exit 0
            ;;
        -t|--type)
            RESTORE_TYPE="$2"
            case $RESTORE_TYPE in
                qdrant)
                    RESTORE_NEO4J=false
                    RESTORE_REDIS=false
                    RESTORE_MONITORING=false
                    ;;
                neo4j)
                    RESTORE_QDRANT=false
                    RESTORE_REDIS=false
                    RESTORE_MONITORING=false
                    ;;
                redis)
                    RESTORE_QDRANT=false
                    RESTORE_NEO4J=false
                    RESTORE_MONITORING=false
                    ;;
                monitoring)
                    RESTORE_QDRANT=false
                    RESTORE_NEO4J=false
                    RESTORE_REDIS=false
                    ;;
                *)
                    error "Unknown restore type: $RESTORE_TYPE"
                    ;;
            esac
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -b, --backup NAME    Backup name to restore"
            echo "  -l, --list           List available backups"
            echo "  -t, --type TYPE      Restore type (qdrant, neo4j, redis, monitoring)"
            echo "  --dry-run           Show what would be restored without doing it"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# ============================================
# Main Restore Process
# ============================================

if [[ -z "$BACKUP_NAME" ]]; then
    log "Error: No backup specified. Use -b to specify backup name."
    list_backups
    exit 1
fi

BACKUP_FILE="${BACKUP_ROOT}/${BACKUP_NAME}"

if [[ ! -e "$BACKUP_FILE" ]]; then
    error "Backup not found: ${BACKUP_FILE}"
fi

log "Starting PROJECT-OMEGA restore..."
log "Backup: ${BACKUP_NAME}"

if [[ "$DRY_RUN" == true ]]; then
    log "*** DRY RUN MODE - No changes will be made ***"
fi

stop_services
extract_backup "${BACKUP_FILE}"
restore_qdrant
restore_neo4j
restore_redis
restore_monitoring
start_services
verify_restore

log "Restore completed successfully!"
notify "Restore completed successfully: ${BACKUP_NAME}" "success"
