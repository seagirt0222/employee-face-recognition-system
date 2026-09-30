#!/bin/bash
set -euo pipefail

echo "🔄 Renewing SSL certificate..."

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod not found"
  exit 1
fi

source .env.prod

DOMAIN="${DOMAIN:-attendance.example.com}"

# Renew certificate
echo "Renewing certificate for ${DOMAIN}..."
docker run --rm \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  -v "$(pwd)/certs-data:/var/www/certbot" \
  certbot/certbot \
  renew --webroot -w /var/www/certbot --quiet || {
    echo "⚠️  Certificate renewal had issues. Checking status..."
    docker run --rm \
      -v "$(pwd)/certs:/etc/letsencrypt" \
      certbot/certbot certificates
  }

# Reload Nginx
echo "Reloading Nginx..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload || {
  echo "⚠️  Nginx reload failed. Restarting..."
  docker compose -f docker-compose.prod.yml restart nginx
}

echo "✅ Certificate renewal complete"
echo ""
echo "Certificate expiration:"
openssl x509 -enddate -noout -in certs/live/${DOMAIN}/fullchain.pem
