#!/bin/bash
set -euo pipefail

echo "💾 Backing up database..."

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

source .env.prod

BACKUP_DIR="./backups"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/attendance_backup_${TIMESTAMP}.sql"

echo "Dumping database to ${BACKUP_FILE}..."
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres -d ${POSTGRES_DB} > "${BACKUP_FILE}"

echo "✅ Backup complete: ${BACKUP_FILE}"
echo "Size: $(du -h "${BACKUP_FILE}" | cut -f1)"
echo ""
echo "Recent backups:"
ls -lh ${BACKUP_DIR}/*.sql 2>/dev/null | tail -5
