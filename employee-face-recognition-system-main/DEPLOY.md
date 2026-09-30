# Nginx 生產部署指南

本指南說明如何使用 Nginx 反向代理、PostgreSQL 和 Docker Compose 將人臉辨識打卡系統部署到生產環境。

## 系統架構

```
Internet
   |
   v
 Nginx (80/443)
   |
   v
Gunicorn + FastAPI (8000)
   |
   v
PostgreSQL (5432)
```

## 前置需求

- Docker & Docker Compose
- Linux 伺服器 (Ubuntu 20.04+ 推薦)
- 域名 (若要 HTTPS)
- 至少 2GB RAM, 20GB 儲存空間

## 快速部署 (本機測試)

### 1. 準備環境

```bash
git clone https://github.com/keithksleeitri/employee-face-recognition-system.git
cd employee-face-recognition-system

# 複製環境設定
cp .env.prod.example .env.prod

# 編輯環境變數
vim .env.prod  # 修改 DB_PASSWORD
```

### 2. 啟動服務

```bash
# 使用 docker-compose.prod.yml 啟動
docker compose -f docker-compose.prod.yml up -d

# 檢查服務狀態
docker compose -f docker-compose.prod.yml ps

# 查看日誌
docker compose -f docker-compose.prod.yml logs -f app
```

### 3. 驗證服務

```bash
# 健康檢查
curl http://localhost:8000/health
curl http://localhost/health  # Through Nginx

# 查看前端
open http://localhost
```

## VPS 部署 (生產環境)

### 1. VPS 準備

```bash
# SSH 連線到 VPS
ssh root@your-vps-ip

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安裝 Docker Compose
sudo apt install docker-compose-plugin

# 驗證
docker --version
docker compose version
```

### 2. 部署應用

```bash
# 克隆專案
git clone https://github.com/keithksleeitri/employee-face-recognition-system.git /opt/face-attendance
cd /opt/face-attendance

# 複製並編輯環境文件
cp .env.prod.example .env.prod
sudo vim .env.prod  # 修改敏感資訊

# 生成自簽憑證 (測試用)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes

# 啟動服務
sudo docker compose -f docker-compose.prod.yml up -d

# 檢查狀態
sudo docker compose -f docker-compose.prod.yml ps
```

### 3. 驗證部署

```bash
# 檢查服務健康狀態
curl http://localhost/health

# 查看應用日誌
sudo docker compose -f docker-compose.prod.yml logs -f app

# 查看資料庫日誌
sudo docker compose -f docker-compose.prod.yml logs -f db
```

## HTTPS/SSL 設定

### 使用 Let's Encrypt (推薦)

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 申請憑證
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 複製憑證到 certs 資料夾
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./certs/
sudo chown $(id -u):$(id -g) ./certs/*

# 編輯 Nginx SSL 設定
cp nginx/conf.d/ssl.conf.example nginx/conf.d/ssl.conf
vim nginx/conf.d/ssl.conf  # 修改域名

# 重新啟動 Nginx
sudo docker compose -f docker-compose.prod.yml restart nginx
```

### 自動更新憑證

```bash
# 建立 crontab
sudo crontab -e

# 加入以下行
0 0 1 * * certbot renew --quiet && docker compose -f /opt/face-attendance/docker-compose.prod.yml restart nginx
```

## 監控與維護

### 查看日誌

```bash
# 應用日誌
sudo tail -f logs/app.log

# Nginx 日誌
sudo tail -f logs/nginx/access.log

# 資料庫日誌
sudo docker compose -f docker-compose.prod.yml logs db
```

### 資料庫備份

```bash
# 備份資料庫
sudo docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres attendance > backup_$(date +%Y%m%d_%H%M%S).sql

# 復原資料庫
cat backup_20240101_120000.sql | sudo docker compose -f docker-compose.prod.yml exec -T db psql -U postgres
```

### 性能監控

```bash
# 查看容器資源使用
docker stats

# 查看磁碟空間
df -h

# 清理無用的 Docker 資源
sudo docker system prune -a
```

## 常見問題

### 1. 資料庫連接失敗

```bash
# 檢查 .env.prod 中的密碼
# 確認資料庫容器正常執行
sudo docker compose -f docker-compose.prod.yml ps

# 檢查資料庫日誌
sudo docker compose -f docker-compose.prod.yml logs db
```

### 2. Nginx 無法連接應用

```bash
# 確認應用容器正常
sudo docker compose -f docker-compose.prod.yml ps app

# 檢查應用日誌
sudo docker compose -f docker-compose.prod.yml logs app

# 測試應用端口
sudo netstat -tlnp | grep 8000
```

### 3. 上傳文件太大失敗

```bash
# 在 docker-compose.prod.yml 中增加環境變數
- UPLOAD_MAX_SIZE=100M  # Nginx client_max_body_size 已設為 50M
```

## 安全建議

1. **更改預設密碼**
   ```bash
   # .env.prod 中更改 DB_PASSWORD
   DB_PASSWORD=$(openssl rand -base64 32)
   ```

2. **防火牆設定**
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **定期備份**
   ```bash
   0 2 * * * /opt/face-attendance/backup.sh
   ```

4. **監控日誌**
   ```bash
   # 設定日誌輪轉
   cat > /etc/logrotate.d/face-attendance << EOF
   /opt/face-attendance/logs/*.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
   }
   EOF
   ```

## 更新應用

```bash
cd /opt/face-attendance

# 拉取最新代碼
git pull origin main

# 重建容器
sudo docker compose -f docker-compose.prod.yml up --build -d

# 驗證
sudo docker compose -f docker-compose.prod.yml ps
```

## 停止/移除服務

```bash
# 停止服務
sudo docker compose -f docker-compose.prod.yml down

# 停止並移除數據
sudo docker compose -f docker-compose.prod.yml down -v
```

## 支援與問題

- GitHub Issues: https://github.com/keithksleeitri/employee-face-recognition-system/issues
- 文件: https://github.com/keithksleeitri/employee-face-recognition-system/wiki
