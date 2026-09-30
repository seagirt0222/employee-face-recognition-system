#!/bin/bash
set -euo pipefail

echo "🔐 Requesting SSL certificate from Let's Encrypt..."

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

source .env.prod

DOMAIN="${DOMAIN:-attendance.example.com}"
EMAIL="${EMAIL:-admin@example.com}"

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Create necessary directories
mkdir -p certs certs-data

# Stop Nginx temporarily to avoid port conflicts
echo "Stopping Nginx..."
docker compose -f docker-compose.prod.yml stop nginx || true

# Request certificate
echo "Requesting certificate..."
docker run --rm \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  -v "$(pwd)/certs-data:/var/www/certbot" \
  -p 80:80 \
  certbot/certbot \
  certonly --standalone \
  -d "${DOMAIN}" \
  --email "${EMAIL}" \
  --agree-tos \
  --non-interactive || {
    echo "❌ Certificate request failed"
    exit 1
  }

echo "✅ Certificate obtained successfully"
echo ""

# Verify certificate exists
if [ ! -f "certs/live/${DOMAIN}/fullchain.pem" ]; then
  echo "❌ Certificate file not found at certs/live/${DOMAIN}/fullchain.pem"
  exit 1
fi

echo "📁 Certificate location: certs/live/${DOMAIN}/"
echo "  - fullchain.pem"
echo "  - privkey.pem"
echo ""

# Start Nginx again
echo "Starting Nginx with certificate..."
docker compose -f docker-compose.prod.yml up -d nginx

sleep 3

# Test HTTPS connection
echo "Testing HTTPS connection..."
if curl -fsS https://${DOMAIN}/health > /dev/null 2>&1; then
  echo "✅ HTTPS connection successful"
else
  echo "⚠️  HTTPS connection test failed. Check Nginx logs:"
  docker compose -f docker-compose.prod.yml logs nginx
fi

echo ""
echo "✅ Certificate setup complete!"
echo ""
echo "Certificate valid until:"
openssl x509 -enddate -noout -in certs/live/${DOMAIN}/fullchain.pem
