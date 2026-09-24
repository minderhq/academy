#!/bin/bash
# PROJECT-OMEGA Backup Script
# Automated backup for all services and data

set -e

# ============================================
# Configuration
# ============================================
BACKUP_ROOT="/volume1/backup/project-omega"
DATA_ROOT="/volume1/docker/project-omega"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="omega_backup_${TIMESTAMP}"
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_NAME}"

# Retention settings
RETENTION_DAYS=30
RETENTION_COUNT=10

# Backup types
BACKUP_TYPE="full"  # full, incremental, pre-deploy
COMPRESS=true
ENCRYPT=false

# Remote backup settings (optional)
REMOTE_ENABLED=false
REMOTE_PATH="rsync://backup-server/omega"
REMOTE_KEY="/root/.ssh/backup_key"

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
    notify "Backup failed: $1" "error"
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

create_backup_dir() {
    log "Creating backup directory: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}/"{data,configs,database,logs}
}

backup_docker_configs() {
    log "Backing up Docker configurations..."
    cp -r "${DATA_ROOT}"/docker-compose*.yml "${BACKUP_DIR}/configs/" 2>/dev/null || true
    cp -r "${DATA_ROOT}"/configs "${BACKUP_DIR}/configs/" 2>/dev/null || true
}

backup_qdrant() {
    log "Backing up Qdrant data..."
    if [[ -d "${DATA_ROOT}/data/qdrant" ]]; then
        # Export snapshots via API
        docker exec project-omega-qdrant \
            curl -X POST http://localhost:6333/collections/snapshots 2>/dev/null || true

        # Copy data directory
        rsync -av --delete "${DATA_ROOT}/data/qdrant/" "${BACKUP_DIR}/data/qdrant/"
    fi
}

backup_neo4j() {
    log "Backing up Neo4j data..."

    if docker ps | grep -q project-omega-neo4j; then
        # Online backup using neo4j-admin
        docker exec project-omega-neo4j \
            neo4j-admin database dump neo4j --to-path=/backups/ 2>/dev/null || true

        # Copy backup files
        find "${DATA_ROOT}/data/neo4j" -name "*.backup" -exec cp {} "${BACKUP_DIR}/database/" \; 2>/dev/null || true

        # Copy data directory
        rsync -av --delete "${DATA_ROOT}/data/neo4j/data/" "${BACKUP_DIR}/data/neo4j/" 2>/dev/null || true
    fi
}

backup_redis() {
    log "Backing up Redis data..."

    if docker ps | grep -q project-omega-redis; then
        # Create Redis backup
        docker exec project-omega-redis \
            redis-cli --rdb /tmp/dump.rdb BGSAVE 2>/dev/null || true

        # Wait for backup to complete
        sleep 5

        # Copy backup file
        docker cp project-omega-redis:/tmp/dump.rdb "${BACKUP_DIR}/database/redis.rdb" 2>/dev/null || true

        # Copy data directory
        rsync -av --delete "${DATA_ROOT}/data/redis/" "${BACKUP_DIR}/data/redis/" 2>/dev/null || true
    fi
}

backup_monitoring() {
    log "Backing up monitoring data..."

    # Prometheus data
    if [[ -d "${DATA_ROOT}/data/prometheus" ]]; then
        rsync -av --delete "${DATA_ROOT}/data/prometheus/" "${BACKUP_DIR}/data/prometheus/"
    fi

    # Grafana data
    if [[ -d "${DATA_ROOT}/data/grafana" ]]; then
        rsync -av --delete "${DATA_ROOT}/data/grafana/" "${BACKUP_DIR}/data/grafana/"
    fi

    # Loki data
    if [[ -d "${DATA_ROOT}/data/loki" ]]; then
        rsync -av --delete "${DATA_ROOT}/data/loki/" "${BACKUP_DIR}/data/loki/"
    fi
}

backup_logs() {
    log "Backing up logs..."

    # Container logs
    docker logs project-omega-qdrant --tail 1000 > "${BACKUP_DIR}/logs/qdrant.log" 2>&1 || true
    docker logs project-omega-neo4j --tail 1000 > "${BACKUP_DIR}/logs/neo4j.log" 2>&1 || true
    docker logs project-omega-redis --tail 1000 > "${BACKUP_DIR}/logs/redis.log" 2>&1 || true
    docker logs project-omega-grafana --tail 1000 > "${BACKUP_DIR}/logs/grafana.log" 2>&1 || true
    docker logs project-omega-prometheus --tail 1000 > "${BACKUP_DIR}/logs/prometheus.log" 2>&1 || true

    # Nginx logs
    if [[ -d "${DATA_ROOT}/nginx/logs" ]]; then
        cp -r "${DATA_ROOT}/nginx/logs/" "${BACKUP_DIR}/logs/nginx/" 2>/dev/null || true
    fi
}

compress_backup() {
    if [[ "$COMPRESS" == true ]]; then
        log "Compressing backup..."
        cd "${BACKUP_ROOT}"
        tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
        rm -rf "${BACKUP_DIR}"
        BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_NAME}.tar.gz"
    fi
}

encrypt_backup() {
    if [[ "$ENCRYPT" == true ]] && [[ -n "${BACKUP_ENCRYPTION_KEY}" ]]; then
        log "Encrypting backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "${BACKUP_DIR}.tar.gz" \
            -out "${BACKUP_DIR}.tar.gz.enc" \
            -k "${BACKUP_ENCRYPTION_KEY}"
        rm "${BACKUP_DIR}.tar.gz"
        BACKUP_DIR="${BACKUP_DIR}.tar.gz.enc"
    fi
}

sync_remote() {
    if [[ "$REMOTE_ENABLED" == true ]]; then
        log "Syncing to remote backup..."
        rsync -avz --delete \
            -e "ssh -i ${REMOTE_KEY}" \
            "${BACKUP_DIR}" \
            "${REMOTE_PATH}/"
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Remove backups older than RETENTION_DAYS
    find "${BACKUP_ROOT}" -name "omega_backup_*" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "${BACKUP_ROOT}" -name "omega_backup_*" -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null || true

    # Keep only RETENTION_COUNT most recent backups
    ls -t "${BACKUP_ROOT}"/omega_backup_*.* 2>/dev/null | tail -n +$((RETENTION_COUNT + 1)) | xargs rm -f 2>/dev/null || true
}

create_backup_manifest() {
    log "Creating backup manifest..."

    cat > "${BACKUP_ROOT}/${BACKUP_NAME}_manifest.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "backup_type": "${BACKUP_TYPE}",
    "backup_path": "${BACKUP_DIR}",
    "size_bytes": $(du -sb "${BACKUP_DIR}" | cut -f1),
    "services": [
        "qdrant",
        "neo4j",
        "redis",
        "grafana",
        "prometheus",
        "loki"
    ],
    "compressed": ${COMPRESS},
    "encrypted": ${ENCRYPT}
}
EOF
}

# ============================================
# Parse Arguments
# ============================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        -n|--no-compress)
            COMPRESS=false
            shift
            ;;
        -e|--encrypt)
            ENCRYPT=true
            shift
            ;;
        --remote)
            REMOTE_ENABLED=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --type TYPE      Backup type (full, incremental, pre-deploy)"
            echo "  -n, --no-compress    Disable compression"
            echo "  -e, --encrypt        Enable encryption"
            echo "  --remote             Enable remote sync"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# ============================================
# Main Backup Process
# ============================================

log "Starting PROJECT-OMEGA backup..."
log "Backup type: ${BACKUP_TYPE}"

create_backup_dir
backup_docker_configs
backup_qdrant
backup_neo4j
backup_redis
backup_monitoring
backup_logs
compress_backup
encrypt_backup
create_backup_manifest
sync_remote
cleanup_old_backups

log "Backup completed successfully!"
log "Backup location: ${BACKUP_DIR}"
notify "Backup completed successfully: ${BACKUP_NAME}" "success"
