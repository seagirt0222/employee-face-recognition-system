#!/bin/bash
set -euo pipefail

echo "⚠️  WARNING: This will stop and remove all containers"
echo "Data in volumes will be preserved."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Cancelled"
  exit 0
fi

echo "Stopping services..."
docker compose -f docker-compose.prod.yml down

echo "✅ Services stopped"
