#!/bin/bash
set -euo pipefail

echo "=== Employee Face Recognition Deployment ==="
echo ""

if [ ! -f .env.prod ]; then
  echo "❌ ERROR: .env.prod not found"
  echo "Please copy from .env.prod.example and configure:"
  echo "  cp .env.prod.example .env.prod"
  echo "  nano .env.prod"
  exit 1
fi

source .env.prod

echo "📋 Configuration:"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "  Database: $POSTGRES_DB"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/uploads logs nginx/conf.d certs certs-data scripts
touch data/uploads/.gitkeep logs/.gitkeep

# Check Docker
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Please install Docker first."
  exit 1
fi
echo "✅ Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
  echo "❌ Docker Compose not found. Please install Docker Compose first."
  exit 1
fi
echo "✅ Docker Compose found"

# Update Nginx SSL config with actual domain
echo "⚙️  Updating Nginx SSL configuration..."
sed -i "s/attendance.example.com/${DOMAIN}/g" nginx/conf.d/ssl.conf

# Build and start services
echo ""
echo "🚀 Building and starting services..."
docker compose -f docker-compose.prod.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check app health
echo "🏥 Checking application health..."
for i in {1..30}; do
  if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "⚠️  Application health check timeout. Check logs:"
    docker compose -f docker-compose.prod.yml logs app
    exit 1
  fi
  echo "  Waiting... ($i/30)"
  sleep 1
done

# Check if certificate exists
echo ""
echo "🔐 Checking SSL certificate..."
if [ ! -f "certs/live/${DOMAIN}/fullchain.pem" ] || [ ! -f "certs/live/${DOMAIN}/privkey.pem" ]; then
  echo "⚠️  No certificate found. Requesting from Let's Encrypt..."
  if [ -f scripts/init-cert.sh ]; then
    chmod +x scripts/init-cert.sh
    DOMAIN="${DOMAIN}" EMAIL="${EMAIL}" bash scripts/init-cert.sh
  else
    echo "❌ init-cert.sh not found"
    exit 1
  fi
else
  echo "✅ Certificate found"
fi

# Restart Nginx to load certificate
echo "🔄 Restarting Nginx..."
docker compose -f docker-compose.prod.yml restart nginx

sleep 3

# Final status check
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📍 Access your application:"
echo "   HTTPS: https://${DOMAIN}"
echo "   HTTP:  http://localhost (redirects to HTTPS)"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:          docker compose -f docker-compose.prod.yml logs -f app"
echo "   Stop services:      docker compose -f docker-compose.prod.yml down"
echo "   Renew certificate:  ./scripts/renew-cert.sh"
echo "   Backup database:    ./scripts/backup.sh"
echo ""
