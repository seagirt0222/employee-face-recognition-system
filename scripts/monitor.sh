#!/bin/bash
set -euo pipefail

echo "📊 System Status and Monitoring"
echo ""

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

source .env.prod

echo "=== Docker Containers ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=== Application Health ==="
if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Application is healthy"
else
  echo "❌ Application health check failed"
fi

echo ""
echo "=== Database Connection ==="
if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
  echo "✅ Database is ready"
else
  echo "❌ Database is not responding"
fi

echo ""
echo "=== SSL Certificate ==="
if [ -f "certs/live/${DOMAIN}/fullchain.pem" ]; then
  echo "Certificate for: ${DOMAIN}"
  openssl x509 -noout -dates -in "certs/live/${DOMAIN}/fullchain.pem"
else
  echo "❌ Certificate not found"
fi

echo ""
echo "=== Disk Space ==="
df -h | grep -E "Filesystem|/$|/var|/home" || df -h

echo ""
echo "=== Recent Logs ==="
echo ""
echo "App (last 10 lines):"
docker compose -f docker-compose.prod.yml logs --tail=10 app 2>/dev/null | head -10 || echo "No logs available"

echo ""
echo "Nginx (last 10 lines):"
docker compose -f docker-compose.prod.yml logs --tail=10 nginx 2>/dev/null | head -10 || echo "No logs available"
