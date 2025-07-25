# 🚀 Guida Deployment Cloud ViralShortsAI

## 📋 **OVERVIEW**
Questa guida ti permette di deployare ViralShortsAI su un server cloud per esecuzione autonoma 24/7.

## 🎯 **COSA OTTIENI**
✅ **Esecuzione 24/7** senza dipendere dal tuo computer
✅ **Dashboard web** per controllo remoto
✅ **API REST** per integrazione
✅ **Monitoring avanzato** con Flower
✅ **Backup automatico** giornaliero
✅ **SSL/HTTPS** automatico con Let's Encrypt
✅ **Auto-restart** in caso di crash
✅ **Logging centralizzato**

## 💰 **COSTI STIMATI**
- **Digital Ocean**: $12/mese (2GB RAM, 1vCPU, 50GB SSD) ⭐ **RACCOMANDATO**
- **AWS EC2**: ~$17/mese (t3.small: 2GB RAM, 2vCPU)
- **Hetzner Cloud**: €4.90/mese (2GB RAM, 1vCPU, 40GB SSD)

## 🚀 **DEPLOYMENT RAPIDO**

### **Opzione 1: Digital Ocean (FACILE)**

#### 1. **Crea Droplet**
```bash
# Sul tuo computer locale
doctl compute droplet create viralshorts \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-2gb \
  --region fra1 \
  --ssh-keys YOUR_SSH_KEY_ID
```

#### 2. **Setup Automatico**
```bash
# Connettiti al server
ssh root@YOUR_DROPLET_IP

# Download e esegui script di setup
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/cloud_deployment/scripts/install.sh | bash
```

### **Opzione 2: Setup Manuale (CONTROLLO COMPLETO)**

#### 1. **Preparazione Server**
```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installa Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Crea utente per l'app
sudo useradd -m -s /bin/bash viralshorts
sudo usermod -aG docker viralshorts
```

#### 2. **Upload Codice**
```bash
# Sul tuo computer locale - crea archivio
cd "/Volumes/RoG Marco 1/Whashing Machine/ViralShortsAI"
tar -czf viralshorts.tar.gz .

# Upload al server
scp viralshorts.tar.gz root@YOUR_SERVER_IP:/tmp/

# Sul server - estrai codice
sudo -u viralshorts mkdir -p /home/viralshorts/app
sudo -u viralshorts tar -xzf /tmp/viralshorts.tar.gz -C /home/viralshorts/app/
```

#### 3. **Configurazione**
```bash
# Sul server
sudo -u viralshorts bash
cd /home/viralshorts/app

# Crea file di configurazione
cat > .env << 'EOF'
# API Keys - SOSTITUISCI CON I TUOI VALORI REALI
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Redis & Database
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///data/viral_shorts.db
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Domain (sostituisci con il tuo dominio)
DOMAIN=your-domain.com
SSL_EMAIL=your-email@example.com
EOF

# Crea directory dati
mkdir -p data/{downloads,processed,uploads,reports,temp}
mkdir -p logs backups
```

#### 4. **Deploy Containers**
```bash
# Build e avvia servizi
docker-compose -f cloud_deployment/docker-compose.yml build
docker-compose -f cloud_deployment/docker-compose.yml up -d

# Verifica status
docker-compose -f cloud_deployment/docker-compose.yml ps
```

## 🔐 **CONFIGURAZIONE SICUREZZA**

### **1. Firewall**
```bash
# Configura UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### **2. SSL Automatico**
```bash
# Se hai un dominio, SSL sarà configurato automaticamente
# Altrimenti accedi via HTTP: http://YOUR_SERVER_IP
```

### **3. Backup Automatico**
```bash
# Configura backup giornaliero (già incluso nel deployment)
crontab -e
# Aggiungi: 0 2 * * * /home/viralshorts/app/backup.sh
```

## 🎛️ **USO DELL'INTERFACCIA WEB**

### **Accesso Dashboard**
```
URL: https://your-domain.com (o http://YOUR_SERVER_IP)

Funzionalità:
🔹 Status sistema in tempo reale
🔹 Controllo daily poster (start/stop)
🔹 Metriche giornaliere
🔹 Forzare posting immediato
🔹 Configurazione parametri
🔹 Visualizzazione logs
```

### **Monitoring Avanzato**
```
URL: https://your-domain.com/monitor/
User: admin
Password: [generata automaticamente - vedi deployment_info.txt]

Funzionalità:
🔹 Queue Celery in tempo reale
🔹 Task history
🔹 Worker status
🔹 Performance metrics
```

## 📊 **COMANDI UTILI**

### **Status e Monitoring**
```bash
# Status tutti i servizi
docker-compose -f cloud_deployment/docker-compose.yml ps

# Logs in tempo reale
docker-compose -f cloud_deployment/docker-compose.yml logs -f

# Logs specifico servizio
docker-compose -f cloud_deployment/docker-compose.yml logs web
docker-compose -f cloud_deployment/docker-compose.yml logs worker
docker-compose -f cloud_deployment/docker-compose.yml logs scheduler

# Accesso container per debug
docker exec -it viralshorts_web bash
```

### **Gestione Servizi**
```bash
# Restart tutti i servizi
docker-compose -f cloud_deployment/docker-compose.yml restart

# Restart servizio specifico
docker-compose -f cloud_deployment/docker-compose.yml restart web

# Stop tutti i servizi
docker-compose -f cloud_deployment/docker-compose.yml down

# Riavvio completo con rebuild
docker-compose -f cloud_deployment/docker-compose.yml down
docker-compose -f cloud_deployment/docker-compose.yml build --no-cache
docker-compose -f cloud_deployment/docker-compose.yml up -d
```

### **Backup e Restore**
```bash
# Backup manuale
./backup.sh

# Lista backup
ls -la backups/

# Restore database (esempio)
docker cp backups/db_20250725_120000.db viralshorts_web:/app/data/viral_shorts.db
docker-compose -f cloud_deployment/docker-compose.yml restart web
```

## 🔧 **TROUBLESHOOTING**

### **Problemi Comuni**

#### **1. Servizi non si avviano**
```bash
# Controlla logs
docker-compose -f cloud_deployment/docker-compose.yml logs

# Controlla spazio disco
df -h

# Controlla memoria
free -h

# Restart forzato
docker-compose -f cloud_deployment/docker-compose.yml down --volumes
docker-compose -f cloud_deployment/docker-compose.yml up -d
```

#### **2. Daily poster non funziona**
```bash
# Controlla worker Celery
docker-compose -f cloud_deployment/docker-compose.yml logs worker

# Controlla scheduler
docker-compose -f cloud_deployment/docker-compose.yml logs scheduler

# Restart worker
docker-compose -f cloud_deployment/docker-compose.yml restart worker scheduler
```

#### **3. Upload non funziona**
```bash
# Verifica API keys in .env
cat .env | grep API_KEY

# Controlla credenziali YouTube
docker exec viralshorts_web ls -la /app/data/youtube_credentials.json

# Test manuale
docker exec viralshorts_web python -c "from main import ViralShortsBackend; backend = ViralShortsBackend(); print('OK')"
```

### **Log Files Importanti**
```bash
# Application logs
tail -f logs/viral_shorts_$(date +%Y-%m-%d).log

# Docker logs
docker-compose -f cloud_deployment/docker-compose.yml logs --tail=100

# System logs
sudo journalctl -u docker -f
```

## 📱 **ACCESSO MOBILE**

L'interfaccia web è responsive e funziona perfettamente su:
- 📱 **Smartphone** (iOS/Android)
- 📲 **Tablet** 
- 💻 **Desktop**

## 🆘 **SUPPORTO**

### **Contatti Debug**
1. **Logs dettagliati**: Sempre disponibili via web dashboard
2. **Monitoring**: Real-time via Flower interface
3. **Health checks**: Endpoint `/health` per status servizi
4. **API documentation**: Endpoint `/api/docs` per Swagger UI

### **Backup Emergency**
```bash
# In caso di problemi critici
./backup.sh
docker-compose -f cloud_deployment/docker-compose.yml down
# Ripristina da backup precedente
```

## 🎉 **RISULTATO FINALE**

Dopo il deployment avrai:

✅ **Sistema completamente autonomo** che funziona 24/7
✅ **Dashboard web professionale** per controllo remoto
✅ **API REST** per integrazioni future
✅ **Monitoring completo** con metriche real-time
✅ **Backup automatico** per sicurezza dati
✅ **SSL/HTTPS** per sicurezza connessioni
✅ **Auto-scaling** e recovery automatico

**Il tuo ViralShortsAI sarà operativo in cloud e pubblicherà video automaticamente ogni giorno senza alcun intervento manuale!** 🚀✨
