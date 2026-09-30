#!/bin/bash
set -euo pipefail

echo "Restore database from backup"
echo ""

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

source .env.prod

BACKUP_DIR="./backups"

if [ ! -d "${BACKUP_DIR}" ]; then
  echo "❌ No backups directory found"
  exit 1
fi

echo "Available backups:"
ls -lh ${BACKUP_DIR}/*.sql 2>/dev/null | nl || {
  echo "No backups found"
  exit 1
}

echo ""
read -p "Enter backup number to restore: " backup_num

BACKUP_FILE=$(ls -1 ${BACKUP_DIR}/*.sql 2>/dev/null | sed -n "${backup_num}p")

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "❌ Invalid selection"
  exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Cancelled"
  exit 0
fi

echo "Restoring from ${BACKUP_FILE}..."
cat "${BACKUP_FILE}" | docker compose -f docker-compose.prod.yml exec -T db psql -U postgres

echo "✅ Restore complete"
