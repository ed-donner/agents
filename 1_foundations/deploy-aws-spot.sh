#!/bin/bash
# IntellaPersona - AWS Spot Instance Deployment Script
# =====================================================

set -e  # Exit on error

echo "🚀 IntellaPersona - AWS Spot Deployment"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="intellapersona"
APP_PORT=7860
DOMAIN="${DOMAIN:-}"  # Optional: Set your domain

# Step 1: Update system
echo -e "${BLUE}📦 Step 1: Updating system...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install Docker
echo -e "${BLUE}🐳 Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Step 3: Install Docker Compose
echo -e "${BLUE}📦 Step 3: Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Step 4: Create application directory
echo -e "${BLUE}📁 Step 4: Setting up application directory...${NC}"
mkdir -p /home/ubuntu/$APP_NAME
cd /home/ubuntu/$APP_NAME

# Step 5: Set up environment variables
echo -e "${BLUE}🔐 Step 5: Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cat > .env << EOF
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# PushOver (Optional)
PUSHOVER_USER_KEY=
PUSHOVER_API_TOKEN=
EOF
    echo -e "${RED}⚠️  IMPORTANT: Edit .env file and add your OPENAI_API_KEY!${NC}"
    echo -e "${RED}   Run: nano .env${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 6: Upload application files (manual step)
echo -e "${BLUE}📤 Step 6: Upload application files${NC}"
echo -e "${RED}⚠️  MANUAL STEP REQUIRED:${NC}"
echo ""
echo "From your local machine, run:"
echo ""
echo -e "${GREEN}  scp -i your-key.pem app_new.py ubuntu@YOUR_IP:/home/ubuntu/$APP_NAME/${NC}"
echo -e "${GREEN}  scp -i your-key.pem requirements.txt ubuntu@YOUR_IP:/home/ubuntu/$APP_NAME/${NC}"
echo -e "${GREEN}  scp -i your-key.pem Dockerfile ubuntu@YOUR_IP:/home/ubuntu/$APP_NAME/${NC}"
echo -e "${GREEN}  scp -i your-key.pem docker-compose.yml ubuntu@YOUR_IP:/home/ubuntu/$APP_NAME/${NC}"
echo -e "${GREEN}  scp -r -i your-key.pem me/ ubuntu@YOUR_IP:/home/ubuntu/$APP_NAME/${NC}"
echo ""
echo "Or use Git:"
echo -e "${GREEN}  git clone YOUR_REPO_URL .${NC}"
echo ""
echo "Press Enter when files are uploaded..."
read

# Step 7: Build and run
echo -e "${BLUE}🏗️  Step 7: Building Docker image...${NC}"
docker-compose build

echo -e "${BLUE}🚀 Step 8: Starting application...${NC}"
docker-compose up -d

# Step 9: Configure firewall
echo -e "${BLUE}🔒 Step 9: Configuring firewall...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow $APP_PORT/tcp  # Gradio
sudo ufw --force enable

# Step 10: Set up Nginx reverse proxy (optional but recommended)
echo -e "${BLUE}🌐 Step 10: Setting up Nginx reverse proxy...${NC}"
if [ ! -z "$DOMAIN" ]; then
    sudo apt-get install -y nginx certbot python3-certbot-nginx
    
    cat > /tmp/nginx-$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    sudo mv /tmp/nginx-$APP_NAME /etc/nginx/sites-available/$APP_NAME
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    # Get SSL certificate
    echo -e "${BLUE}🔒 Setting up SSL certificate...${NC}"
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    echo -e "${GREEN}✅ Nginx configured with SSL for $DOMAIN${NC}"
else
    echo -e "${BLUE}ℹ️  No domain specified. Access via IP: http://YOUR_IP:$APP_PORT${NC}"
fi

# Step 11: Set up auto-restart on spot interruption
echo -e "${BLUE}🔄 Step 11: Setting up auto-restart...${NC}"
cat > /home/ubuntu/check-spot.sh << 'EOF'
#!/bin/bash
# Check for spot instance interruption
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
if curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/spot/instance-action | grep -q action; then
    echo "Spot instance terminating, saving state..."
    docker-compose -f /home/ubuntu/intellapersona/docker-compose.yml down
fi
EOF

chmod +x /home/ubuntu/check-spot.sh

# Add to crontab (check every minute)
(crontab -l 2>/dev/null; echo "* * * * * /home/ubuntu/check-spot.sh") | crontab -

echo -e "${GREEN}✅ Auto-restart configured${NC}"

# Final status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 Status Check:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}📱 Access your app:${NC}"
if [ ! -z "$DOMAIN" ]; then
    echo -e "  🌐 https://$DOMAIN"
else
    echo -e "  🌐 http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):$APP_PORT"
fi

echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo -e "  View logs:    ${GREEN}docker-compose logs -f${NC}"
echo -e "  Restart:      ${GREEN}docker-compose restart${NC}"
echo -e "  Stop:         ${GREEN}docker-compose down${NC}"
echo -e "  Update:       ${GREEN}git pull && docker-compose up -d --build${NC}"
echo ""
echo -e "${RED}⚠️  Don't forget to edit .env with your OPENAI_API_KEY!${NC}"
echo -e "  Run: ${GREEN}nano /home/ubuntu/$APP_NAME/.env${NC}"
echo ""
