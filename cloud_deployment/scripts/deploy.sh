#!/bin/bash

# 🚀 ViralShortsAI Cloud Deployment Script
# Script automatico per deploy su server cloud

set -e  # Exit on any error

echo "🚀 ViralShortsAI Cloud Deployment Starting..."
echo "================================================"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzioni helper
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Controllo prerequisiti
log_info "Controllo prerequisiti..."

if ! command -v docker &> /dev/null; then
    log_error "Docker non installato. Installalo prima di continuare."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose non installato. Installalo prima di continuare."
    exit 1
fi

log_success "Prerequisiti OK"

# Configurazione
APP_NAME="viralshorts"
DOMAIN=${1:-"localhost"}
SSL_EMAIL=${2:-"admin@example.com"}

log_info "Configurazione deployment:"
log_info "  - App Name: $APP_NAME"
log_info "  - Domain: $DOMAIN"
log_info "  - SSL Email: $SSL_EMAIL"

# Crea directory di lavoro
WORK_DIR="/opt/$APP_NAME"
log_info "Creazione directory di lavoro: $WORK_DIR"

sudo mkdir -p $WORK_DIR
sudo chown $USER:$USER $WORK_DIR
cd $WORK_DIR

# Download del progetto (sostituire con il tuo repository)
log_info "Download codice applicazione..."

if [ ! -d "ViralShortsAI" ]; then
    # Per ora copiamo i file locali
    log_warning "Copying local files (in production use git clone)"
    cp -r /path/to/local/ViralShortsAI .
else
    log_info "Aggiornamento codice esistente..."
    cd ViralShortsAI
    # git pull origin main
    cd ..
fi

# Crea file di configurazione ambiente
log_info "Creazione file di configurazione..."

cat > .env << EOF
# 🔐 ViralShortsAI Cloud Environment Configuration

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Database Configuration
DATABASE_URL=sqlite:///data/viral_shorts.db

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Keys (da sostituire con valori reali)
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_CLIENT_ID=your_youtube_client_id_here
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret_here

# Domain Configuration
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
CORS_ORIGINS=["http://localhost:3000", "https://$DOMAIN"]
EOF

log_success "File .env creato"

# Crea directory necessarie
log_info "Creazione directory dati..."
mkdir -p data/{downloads,processed,uploads,reports,temp}
mkdir -p logs
mkdir -p backups

# Crea configurazione Nginx per SSL
log_info "Configurazione Nginx con SSL..."

cat > nginx.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Main Application
    location / {
        proxy_pass http://web:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # API Endpoints
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Monitoring (Flower)
    location /monitor/ {
        proxy_pass http://monitor:5555/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Basic Auth for monitoring
        auth_basic "Monitoring Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

# Crea password per monitoring
log_info "Configurazione autenticazione monitoring..."
MONITOR_PASSWORD=$(openssl rand -base64 12)
echo "admin:$(openssl passwd -apr1 $MONITOR_PASSWORD)" > .htpasswd
log_success "Password monitoring: $MONITOR_PASSWORD"

# Configura SSL con Let's Encrypt (se dominio diverso da localhost)
if [ "$DOMAIN" != "localhost" ]; then
    log_info "Configurazione SSL con Let's Encrypt..."
    
    if ! command -v certbot &> /dev/null; then
        log_info "Installazione Certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    log_info "Ottenimento certificato SSL..."
    sudo certbot certonly --standalone -d $DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive
    
    if [ $? -eq 0 ]; then
        log_success "Certificato SSL ottenuto con successo"
    else
        log_warning "Errore ottenimento SSL, continuando senza HTTPS"
        # Fallback a configurazione HTTP
        cat > nginx.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://web:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /monitor/ {
        proxy_pass http://monitor:5555/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        auth_basic "Monitoring Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF
    fi
fi

# Build e deploy containers
log_info "Build containers Docker..."
cd ViralShortsAI
docker-compose -f cloud_deployment/docker-compose.yml build

if [ $? -eq 0 ]; then
    log_success "Build completato con successo"
else
    log_error "Errore durante il build"
    exit 1
fi

# Avvio servizi
log_info "Avvio servizi..."
docker-compose -f cloud_deployment/docker-compose.yml up -d

if [ $? -eq 0 ]; then
    log_success "Servizi avviati con successo"
else
    log_error "Errore avvio servizi"
    exit 1
fi

# Configura backup automatico
log_info "Configurazione backup automatico..."

cat > backup.sh << EOF
#!/bin/bash
# Backup automatico ViralShortsAI

BACKUP_DIR="$WORK_DIR/backups"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec viralshorts_web cp /app/data/viral_shorts.db /tmp/
docker cp viralshorts_web:/tmp/viral_shorts.db \$BACKUP_DIR/db_\$TIMESTAMP.db

# Backup configurazione
cp $WORK_DIR/.env \$BACKUP_DIR/env_\$TIMESTAMP
cp $WORK_DIR/ViralShortsAI/config.json \$BACKUP_DIR/config_\$TIMESTAMP.json

# Rimuovi backup vecchi (>7 giorni)
find \$BACKUP_DIR -name "*.db" -mtime +7 -delete
find \$BACKUP_DIR -name "env_*" -mtime +7 -delete
find \$BACKUP_DIR -name "config_*" -mtime +7 -delete

echo "Backup completato: \$TIMESTAMP"
EOF

chmod +x backup.sh

# Aggiungi backup al crontab
log_info "Configurazione cron per backup..."
(crontab -l 2>/dev/null; echo "0 2 * * * $WORK_DIR/backup.sh >> $WORK_DIR/logs/backup.log 2>&1") | crontab -

# Configurazione monitoraggio sistema
log_info "Configurazione monitoraggio..."

cat > monitor.sh << EOF
#!/bin/bash
# Script monitoraggio sistema

# Controllo servizi
docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml ps

# Controllo spazio disco
df -h $WORK_DIR

# Controllo memoria
free -h

# Controllo logs
tail -n 50 $WORK_DIR/logs/app.log
EOF

chmod +x monitor.sh

# Test deployment
log_info "Test deployment..."

# Aspetta che i servizi si avviino
sleep 30

# Test connessione
if curl -f http://localhost/health > /dev/null 2>&1; then
    log_success "✅ Deployment completato con successo!"
else
    log_warning "⚠️ Servizi avviati ma test di connessione fallito"
fi

# Riepilogo finale
echo ""
echo "🎉 ================================================"
echo "🎉 DEPLOYMENT COMPLETATO!"
echo "🎉 ================================================"
echo ""
log_info "📋 INFORMAZIONI ACCESSO:"
echo "   🌐 Web Dashboard: http://$DOMAIN (o https://$DOMAIN se SSL abilitato)"
echo "   📊 Monitoring: http://$DOMAIN/monitor/ (user: admin, pass: $MONITOR_PASSWORD)"
echo "   🔗 API: http://$DOMAIN/api/"
echo ""
log_info "📁 DIRECTORY:"
echo "   📂 App: $WORK_DIR/ViralShortsAI"
echo "   💾 Data: $WORK_DIR/data"
echo "   📄 Logs: $WORK_DIR/logs"
echo "   💿 Backup: $WORK_DIR/backups"
echo ""
log_info "🛠️ COMANDI UTILI:"
echo "   📊 Status: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml ps"
echo "   📄 Logs: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml logs -f"
echo "   🔄 Restart: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml restart"
echo "   ⏹️ Stop: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml down"
echo "   🗂️ Backup: $WORK_DIR/backup.sh"
echo ""
log_success "Il sistema è ora operativo 24/7! 🚀"

# Salva info deployment
cat > deployment_info.txt << EOF
ViralShortsAI Cloud Deployment
==============================
Date: $(date)
Domain: $DOMAIN
SSL: $([ "$DOMAIN" != "localhost" ] && echo "Enabled" || echo "Disabled")
Monitor Password: $MONITOR_PASSWORD

URLs:
- Dashboard: http://$DOMAIN
- API: http://$DOMAIN/api/
- Monitoring: http://$DOMAIN/monitor/

Commands:
- Status: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml ps
- Logs: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml logs -f
- Restart: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml restart
- Stop: docker-compose -f $WORK_DIR/ViralShortsAI/cloud_deployment/docker-compose.yml down
- Backup: $WORK_DIR/backup.sh

Files:
- Config: $WORK_DIR/.env
- Data: $WORK_DIR/data/
- Logs: $WORK_DIR/logs/
- Backups: $WORK_DIR/backups/
EOF

log_success "Info deployment salvate in: $WORK_DIR/deployment_info.txt"
