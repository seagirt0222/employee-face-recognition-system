#!/bin/bash
set -euo pipefail

echo "🔄 Updating and restarting services..."

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

echo "Pulling latest code..."
git pull origin main

echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo "Restarting services..."
docker compose -f docker-compose.prod.yml up -d

echo "Waiting for services..."
sleep 10

echo "Checking health..."
if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Update complete and services are healthy"
else
  echo "⚠️  Health check failed. Checking logs:"
  docker compose -f docker-compose.prod.yml logs app
fi
