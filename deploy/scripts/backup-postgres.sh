#!/bin/bash
# ============================================
# PostgreSQL Backup Script
# ============================================
# Usage: ./backup-postgres.sh [backup_dir]
# Run daily via cron: 0 2 * * * /path/to/backup-postgres.sh /backups

set -euo pipefail

BACKUP_DIR="${1:-/backups/postgres}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/text2img_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Perform backup
echo "[$(date)] Starting PostgreSQL backup..."
docker exec t2i_postgres pg_dump \
    -U "${POSTGRES_USER:-text2img}" \
    -d "${POSTGRES_DB:-text2img}" \
    --format=custom \
    --compress=9 \
    > "${BACKUP_FILE}"

# Verify backup
FILESIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}")
if [ "${FILESIZE}" -lt 100 ]; then
    echo "ERROR: Backup file is suspiciously small (${FILESIZE} bytes)"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

echo "[$(date)] Backup complete: ${BACKUP_FILE} (${FILESIZE} bytes)"

# Cleanup old backups
echo "[$(date)] Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "text2img_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup script finished"
