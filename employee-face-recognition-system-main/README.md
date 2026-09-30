# Employee Face Recognition Attendance System

Business-ready employee attendance system with face recognition powered by InsightFace and OpenCV.

## Features

- ✅ Face recognition with InsightFace (ArcFace embedding)
- ✅ Employee registration with multi-face support
- ✅ Real-time attendance check-in/check-out
- ✅ PostgreSQL database for production
- ✅ Nginx reverse proxy with HTTPS/TLS
- ✅ Let's Encrypt automatic certificate management
- ✅ Docker containerized deployment
- ✅ Complete monitoring and logging
- ✅ Automatic daily backups

## Quick Start (Production)

### Prerequisites

- Docker & Docker Compose installed
- A public domain name pointing to your server
- Ports 80 and 443 open

### 1. Setup

```bash
git clone https://github.com/keithksleeitri/employee-face-recognition-system.git
cd employee-face-recognition-system

cp .env.prod.example .env.prod
```

### 2. Configure

Edit `.env.prod`:

```bash
nan .env.prod
```

Set your:
- `DB_PASSWORD` - PostgreSQL password
- `DOMAIN` - Your domain (e.g., attendance.example.com)
- `EMAIL` - Admin email for Let's Encrypt

### 3. Deploy

```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

That's it! Your system is now running at:

```
https://your-domain.com
```

## Deployment Architecture

```
Internet
   |
   v
Nginx (port 80/443) - HTTPS + redirect
   |
   v
Gunicorn + FastAPI (port 8000)
   |
   v
PostgreSQL (port 5432)
```

## File Structure

```
.
├── app/                    # FastAPI application
│   ├── main.py            # API endpoints
│   ├── models.py          # SQLAlchemy models
│   ├── face_service.py    # Face recognition logic
│   ├── database.py        # Database setup
│   ├── logging_config.py  # Logging configuration
│   └── static/            # Web dashboard
├── nginx/
│   ├── nginx.conf         # Nginx main config
│   └── conf.d/
│       ├── default.conf   # HTTP redirect
│       └── ssl.conf       # HTTPS config
├── scripts/
│   ├── deploy.sh          # One-click deploy
│   ├── init-cert.sh       # Get Let's Encrypt cert
│   ├── renew-cert.sh      # Renew certificate
│   ├── backup.sh          # Database backup
│   └── monitor.sh         # System monitoring
├── data/
│   └── uploads/           # Employee face images
├── logs/                  # Application logs
├── certs/                 # SSL certificates
├── docker-compose.prod.yml
├── Dockerfile.prod
├── requirements.txt
├── init.sql              # Database initialization
├── .env.prod.example     # Environment template
└── README.md
```

## Common Commands

### View logs

```bash
# Application
docker compose -f docker-compose.prod.yml logs -f app

# Nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Database
docker compose -f docker-compose.prod.yml logs -f db
```

### Health check

```bash
curl https://your-domain.com/health
```

### Backup database

```bash
./scripts/backup.sh
```

### Certificate renewal (manual)

```bash
./scripts/renew-cert.sh
```

### Stop services

```bash
docker compose -f docker-compose.prod.yml down
```

## API Documentation

### Employee Registration

```bash
curl -X POST https://your-domain.com/employees/register \
  -F "employee_id=E001" \
  -F "name=Alice Johnson" \
  -F "department=Engineering" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg"
```

### Attendance Check

```bash
curl -X POST https://your-domain.com/attendance/check \
  -F "photo=@attendance_photo.jpg" \
  -F "mode=check_in" \
  -F "threshold=0.80"
```

### List Employees

```bash
curl https://your-domain.com/employees
```

### View Attendance Records

```bash
curl https://your-domain.com/attendance
```

### Attendance Summary

```bash
curl https://your-domain.com/attendance/summary
```

## Troubleshooting

### Certificate not found

```bash
# Re-request certificate
DOMAIN=your-domain.com EMAIL=your-email@example.com ./scripts/init-cert.sh
```

### Database connection error

```bash
# Check database is running
docker compose -f docker-compose.prod.yml exec db pg_isready
```

### Nginx config error

```bash
# Validate nginx config
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### App crashes on startup

```bash
# View detailed logs
docker compose -f docker-compose.prod.yml logs --tail=100 app
```

## Maintenance

### Automatic certificate renewal

Add to crontab:

```bash
crontab -e
```

Add:

```cron
0 3 * * * /path/to/project/scripts/renew-cert.sh >> /var/log/certbot.log 2>&1
```

### Daily backups

```bash
crontab -e
```

Add:

```cron
0 2 * * * /path/to/project/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## Security Notes

- Change `DB_PASSWORD` to a strong password
- Use environment variables for sensitive data
- Enable firewall rules (only allow 80, 443, and SSH)
- Keep Docker images updated
- Monitor logs regularly

## Performance Tuning

- Gunicorn workers: 4 (in Dockerfile.prod)
- PostgreSQL connections: default 100
- Nginx worker processes: auto
- Face matching threshold: 0.80 (adjustable in .env.prod)

## Technology Stack

- **Backend**: FastAPI + Gunicorn
- **Database**: PostgreSQL 15
- **Reverse Proxy**: Nginx
- **Face Recognition**: InsightFace / ArcFace
- **SSL/TLS**: Let's Encrypt + Certbot
- **Container**: Docker + Docker Compose

## License

MIT

## Support

For issues, create a GitHub issue or check the DEPLOY.md for detailed deployment guide.
