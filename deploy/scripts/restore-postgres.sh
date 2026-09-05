#!/bin/bash
# ============================================
# PostgreSQL Restore Script
# ============================================
# Usage: ./restore-postgres.sh <backup_file.sql.gz>

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -la /backups/postgres/text2img_*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will OVERWRITE the current database!"
read -p "Are you sure? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "[$(date)] Stopping worker..."
docker stop t2i_worker 2>/dev/null || true

echo "[$(date)] Dropping and recreating database..."
docker exec t2i_postgres psql \
    -U "${POSTGRES_USER:-text2img}" \
    -d postgres \
    -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-text2img};"
docker exec t2i_postgres psql \
    -U "${POSTGRES_USER:-text2img}" \
    -d postgres \
    -c "CREATE DATABASE ${POSTGRES_DB:-text2img};"

echo "[$(date)] Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker exec -i t2i_postgres pg_restore \
    -U "${POSTGRES_USER:-text2img}" \
    -d "${POSTGRES_DB:-text2img}" \
    --no-owner \
    --no-acl 2>/dev/null || true

echo "[$(date)] Running migrations..."
docker exec t2i_backend alembic upgrade head

echo "[$(date)] Restarting worker..."
docker start t2i_worker

echo "[$(date)] Restore complete!"
