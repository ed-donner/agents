# 🚀 AWS Spot Instance Deployment Guide
## IntellaPersona - Hızlı Başlangıç

---

## 📋 Gereksinimler

- ✅ AWS hesabı
- ✅ EC2 key pair (.pem dosyası)
- ✅ OpenAI API key
- ✅ Terminal/SSH bilgisi

---

## 💰 Maliyet Tahmini

| Instance Type | vCPU | RAM | Spot Fiyat/saat | Aylık (~) |
|---------------|------|-----|-----------------|-----------|
| **t3.micro** | 2 | 1 GB | $0.002 | **$1.44** |
| **t3.small** | 2 | 2 GB | $0.004 | **$2.88** |
| **t3.medium** | 2 | 4 GB | $0.008 | **$5.76** |

**Öneri:** `t3.small` (2 GB RAM yeterli)

---

## 🚀 Deployment (3 Yöntem)

### Yöntem 1: Otomatik Script (EN KOLAY) ⭐

#### Adım 1: Spot Instance Başlat

AWS Console → EC2 → Launch Instance:

```yaml
Name: intellapersona
AMI: Ubuntu Server 22.04 LTS
Instance type: t3.small
Key pair: your-key.pem

Network settings:
  - Allow SSH (22)
  - Allow HTTP (80)
  - Allow HTTPS (443)
  - Allow Custom TCP (7860)

Storage: 20 GB gp3

Advanced > Request Spot instances: ✅
```

**Launch Instance!**

#### Adım 2: SSH ile Bağlan

```bash
# Local makinenden
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

#### Adım 3: Dosyaları Upload Et

**Terminal 1 (Local):**
```bash
cd /Users/gonenc_aydin/Desktop/The_Complete_AI_Agent_Course/agents/1_foundations

# Upload files
scp -i your-key.pem app_new.py ubuntu@YOUR_EC2_IP:~/
scp -i your-key.pem requirements.txt ubuntu@YOUR_EC2_IP:~/
scp -i your-key.pem Dockerfile ubuntu@YOUR_EC2_IP:~/
scp -i your-key.pem docker-compose.yml ubuntu@YOUR_EC2_IP:~/
scp -i your-key.pem deploy-aws-spot.sh ubuntu@YOUR_EC2_IP:~/
scp -r -i your-key.pem me/ ubuntu@YOUR_EC2_IP:~/
```

#### Adım 4: Script Çalıştır

**Terminal 2 (EC2):**
```bash
chmod +x deploy-aws-spot.sh
sudo ./deploy-aws-spot.sh
```

#### Adım 5: API Key Ekle

```bash
nano .env

# Düzenle:
OPENAI_API_KEY=sk-your-actual-key-here
```

**Ctrl+X → Y → Enter** (kaydet)

#### Adım 6: Restart

```bash
docker-compose restart
```

#### Adım 7: Test Et

```bash
# Logs kontrol
docker-compose logs -f

# Browser'da aç
http://YOUR_EC2_IP:7860
```

**✅ TAMAMLANDI!**

---

### Yöntem 2: Manuel Docker (Kontrol İstersen)

#### Adım 1-3: Yukarıdaki gibi (Instance + SSH + Upload)

#### Adım 4: Docker Kur

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

#### Adım 5: Build & Run

```bash
# Create .env
cat > .env << EOF
OPENAI_API_KEY=sk-your-actual-key-here
PUSHOVER_USER_KEY=
PUSHOVER_API_TOKEN=
EOF

# Build
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Adım 6: Access

```bash
http://YOUR_EC2_IP:7860
```

---

### Yöntem 3: Direct Python (Docker Olmadan)

#### Adım 1-3: Yukarıdaki gibi (Instance + SSH + Upload)

#### Adım 4: Python Setup

```bash
# Install Python 3.10
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="sk-your-actual-key-here"

# Run app
nohup python3 app_new.py > app.log 2>&1 &
```

#### Adım 5: Access

```bash
http://YOUR_EC2_IP:7860
```

---

## 🌐 Custom Domain Ekle (Optional)

### Adım 1: Nginx Kur

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### Adım 2: Nginx Config

```bash
sudo nano /etc/nginx/sites-available/intellapersona
```

**Yapıştır:**
```nginx
server {
    listen 80;
    server_name intellapersona.com;  # Your domain

    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Adım 3: Enable & Reload

```bash
sudo ln -s /etc/nginx/sites-available/intellapersona /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Adım 4: SSL (HTTPS)

```bash
sudo certbot --nginx -d intellapersona.com -d www.intellapersona.com
```

**✅ https://intellapersona.com** artık çalışıyor!

---

## 🔄 Monitoring & Maintenance

### Logs

```bash
# Docker logs
docker-compose logs -f

# App logs (if using direct Python)
tail -f app.log
```

### Restart

```bash
# Docker
docker-compose restart

# Direct Python
pkill -f app_new.py
nohup python3 app_new.py > app.log 2>&1 &
```

### Update

```bash
# If using Git
git pull
docker-compose up -d --build

# If using SCP
# Upload new app_new.py
scp -i your-key.pem app_new.py ubuntu@YOUR_EC2_IP:~/
docker-compose restart
```

### Spot Instance Interruption Check

```bash
# Auto-check script already configured
# Check crontab
crontab -l
```

---

## 💡 Best Practices

### 1. Elastic IP (Recommended)

```bash
# AWS Console → EC2 → Elastic IPs
# Allocate new address
# Associate with your instance
# Now your IP won't change!
```

### 2. Auto-Scaling (Advanced)

```bash
# Use AWS Auto Scaling Group
# Min: 1, Max: 1, Desired: 1
# Automatically replaces terminated spot instances
```

### 3. Database Backup

```bash
# Backup SQLite DB daily
0 2 * * * docker exec intellapersona cp /app/career_bot.db /app/data/backup_$(date +\%Y\%m\%d).db
```

### 4. CloudWatch Monitoring

```bash
# Enable detailed monitoring in EC2
# Set up alarms for:
# - CPU > 80%
# - Spot interruption warnings
# - Health check failures
```

---

## 🆘 Troubleshooting

### Build Failed

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### App Not Accessible

```bash
# Check if running
docker-compose ps

# Check firewall
sudo ufw status

# Check port
sudo netstat -tulpn | grep 7860
```

### Out of Memory

```bash
# Add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Spot Interrupted

```bash
# AWS automatically terminates
# Use Auto Scaling Group to auto-replace
# Or manually launch new spot instance
# Database is saved if you used volumes
```

---

## 📊 Cost Optimization

### 1. Use Spot Fleet

```bash
# Mix of t3.micro, t3.small, t3a.small
# AWS automatically picks cheapest
```

### 2. Schedule On/Off

```bash
# Stop at night (if not 24/7)
# Use Lambda + EventBridge
# Start: 8 AM, Stop: 11 PM
# Save ~50% cost
```

### 3. Reserved Capacity (If stable)

```bash
# After 1 month, if stable usage
# Switch to Savings Plans
# Save additional 30-40%
```

---

## 🎯 Quick Commands Reference

```bash
# Deploy
sudo ./deploy-aws-spot.sh

# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Update
git pull && docker-compose up -d --build

# Backup DB
docker exec intellapersona cp /app/career_bot.db /app/data/backup.db

# Shell into container
docker exec -it intellapersona bash
```

---

## ✅ Checklist

- [ ] EC2 Spot instance başlatıldı (t3.small)
- [ ] Security Group configured (22, 80, 443, 7860)
- [ ] SSH connection başarılı
- [ ] Dosyalar upload edildi (app_new.py, me/, etc.)
- [ ] Docker & Docker Compose kuruldu
- [ ] .env file oluşturuldu (OPENAI_API_KEY eklendi)
- [ ] Docker container başlatıldı
- [ ] Health check başarılı (http://IP:7860)
- [ ] (Optional) Custom domain configured
- [ ] (Optional) SSL certificate installed
- [ ] (Optional) Auto-scaling configured

---

## 🎉 Sonuç

**AWS Spot ile:**
- ✅ $2-5/ay maliyet
- ✅ Tam kontrol
- ✅ Hızlı (cold start yok)
- ✅ Custom domain
- ✅ 24/7 uptime

**vs Hugging Face:**
- HF: Ücretsiz ama yavaş + cold start
- AWS: Çok ucuz + süper hızlı ⚡

**İkisini de kullan!**
- HF: Public demo, portfolio
- AWS: Production, müşteri demoları

---

## 📞 Support

Sorun olursa:
1. Logs kontrol et: `docker-compose logs -f`
2. GitHub issues aç
3. AWS Support başvur

**Good luck! 🚀**
