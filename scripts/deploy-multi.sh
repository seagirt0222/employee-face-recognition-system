#!/bin/bash
set -euo pipefail

echo "=== Multi-device Face Recognition Deployment ==="

if [ ! -f .env.prod ]; then
  echo "Missing .env.prod. Please configure environment first."
  exit 1
fi

source .env.prod

mkdir -p logs data/uploads

echo "Starting central stack and edge devices..."
docker compose -f docker-compose.multi.yml up --build -d

echo "Waiting for services to start..."
sleep 10

echo "Health check:"
curl -fsS http://localhost:8000/health || true

echo ""
echo "Services started."
echo "API: http://localhost:8000"
echo "HTTPS via Nginx: https://attendance.u-ark.com"
echo "Device 01: device-01"
echo "Device 02: device-02"
