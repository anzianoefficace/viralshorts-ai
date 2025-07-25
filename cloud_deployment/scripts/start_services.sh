#!/bin/bash

# 🚀 ViralShortsAI Cloud Services Startup Script
# Avvia tutti i servizi necessari per il funzionamento in cloud

set -e

echo "🚀 Starting ViralShortsAI Cloud Services..."

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Funzione per aspettare che un servizio sia pronto
wait_for_service() {
    local service=$1
    local port=$2
    local timeout=${3:-30}
    
    log_info "Waiting for $service to be ready on port $port..."
    
    for i in $(seq 1 $timeout); do
        if nc -z localhost $port 2>/dev/null; then
            log_success "$service is ready!"
            return 0
        fi
        sleep 1
    done
    
    log_error "$service failed to start within $timeout seconds"
    return 1
}

# Controlla se è la prima esecuzione
FIRST_RUN=false
if [ ! -f "/app/.initialized" ]; then
    FIRST_RUN=true
fi

# Setup iniziale solo al primo avvio
if [ "$FIRST_RUN" = true ]; then
    log_info "First run detected, performing initial setup..."
    
    # Crea directory necessarie
    mkdir -p /app/data/{downloads,processed,uploads,reports,temp}
    mkdir -p /app/logs
    mkdir -p /app/static
    
    # Imposta permessi
    chown -R viralshorts:viralshorts /app/data
    chown -R viralshorts:viralshorts /app/logs
    
    # Inizializza database
    log_info "Initializing database..."
    python -c "
from database import Database
db = Database('/app/data/viral_shorts.db')
db.close()
print('Database initialized successfully')
"
    
    # Segna come inizializzato
    touch /app/.initialized
    log_success "Initial setup completed"
fi

# Avvia Redis (se non già in esecuzione)
log_info "Starting Redis..."
redis-server --daemonize yes --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

# Aspetta che Redis sia pronto
wait_for_service "Redis" 6379

# Avvia Celery Worker in background
log_info "Starting Celery Worker..."
celery -A cloud_deployment.celery_app worker --loglevel=info --detach \
    --pidfile=/tmp/celery_worker.pid \
    --logfile=/app/logs/celery_worker.log

# Aspetta che worker sia inizializzato
sleep 5

# Avvia Celery Beat (scheduler) in background
log_info "Starting Celery Beat (Scheduler)..."
celery -A cloud_deployment.celery_app beat --loglevel=info --detach \
    --pidfile=/tmp/celery_beat.pid \
    --logfile=/app/logs/celery_beat.log

# Aspetta che scheduler sia inizializzato
sleep 3

# Avvia Flower (monitoring) in background
log_info "Starting Flower (Monitoring)..."
celery -A cloud_deployment.celery_app flower --port=5555 --detach \
    --pidfile=/tmp/flower.pid \
    --logfile=/app/logs/flower.log

# Aspetta che Flower sia pronto
wait_for_service "Flower" 5555

# Avvia API Server (FastAPI) in background
log_info "Starting API Server..."
uvicorn cloud_deployment.api.main:app --host 0.0.0.0 --port 8000 \
    --log-level info --access-log \
    --log-config /app/cloud_deployment/config/logging.yaml &

# Aspetta che API sia pronta
wait_for_service "API Server" 8000

# Configura e avvia Nginx
log_info "Configuring Nginx..."

# Copia configurazione personalizzata se esiste
if [ -f "/app/cloud_deployment/config/nginx.conf" ]; then
    cp /app/cloud_deployment/config/nginx.conf /etc/nginx/sites-available/default
fi

# Test configurazione Nginx
nginx -t
if [ $? -eq 0 ]; then
    log_success "Nginx configuration is valid"
else
    log_error "Nginx configuration error"
    exit 1
fi

# Avvia Nginx
log_info "Starting Nginx..."
nginx -g "daemon off;" &

# Aspetta che Nginx sia pronto
wait_for_service "Nginx" 80

# Avvia l'applicazione Flask principale
log_info "Starting Flask Web Application..."
export FLASK_ENV=production
export FLASK_APP=cloud_deployment.web_app:app

# Usa Gunicorn per produzione
gunicorn --bind 0.0.0.0:5000 \
         --workers 2 \
         --worker-class gevent \
         --worker-connections 1000 \
         --timeout 120 \
         --keepalive 2 \
         --preload \
         --log-level info \
         --access-logfile /app/logs/gunicorn_access.log \
         --error-logfile /app/logs/gunicorn_error.log \
         --capture-output \
         --enable-stdio-inheritance \
         cloud_deployment.web_app:app &

# Aspetta che Flask sia pronta
wait_for_service "Flask App" 5000

# Avvia Daily Auto Poster
log_info "Initializing Daily Auto Poster..."
python -c "
import sys
sys.path.append('/app')
from daily_auto_poster import DailyAutoPoster
from main import ViralShortsBackend

try:
    backend = ViralShortsBackend()
    if hasattr(backend, 'daily_poster') and backend.daily_poster:
        backend.daily_poster.start()
        print('Daily Auto Poster started successfully')
    else:
        print('Daily Auto Poster not available')
except Exception as e:
    print(f'Error starting Daily Auto Poster: {e}')
"

# Setup di monitoraggio e health checks
log_info "Setting up health monitoring..."

# Crea script di health check
cat > /app/health_check.sh << 'EOF'
#!/bin/bash
# Health check script

# Controlla tutti i servizi critici
SERVICES=("Redis:6379" "Flask:5000" "API:8000" "Flower:5555" "Nginx:80")
ALL_OK=true

for service in "${SERVICES[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if ! nc -z localhost $port 2>/dev/null; then
        echo "❌ $name (port $port) is not responding"
        ALL_OK=false
    else
        echo "✅ $name (port $port) is healthy"
    fi
done

if [ "$ALL_OK" = true ]; then
    echo "🎉 All services are healthy"
    exit 0
else
    echo "⚠️ Some services have issues"
    exit 1
fi
EOF

chmod +x /app/health_check.sh

# Configura cron per monitoraggio
cat > /tmp/monitoring_cron << 'EOF'
# Health check ogni 5 minuti
*/5 * * * * /app/health_check.sh >> /app/logs/health_check.log 2>&1

# Cleanup logs vecchi ogni giorno alle 2:00
0 2 * * * find /app/logs -name "*.log" -mtime +7 -delete

# Backup automatico database ogni giorno alle 3:00
0 3 * * * cp /app/data/viral_shorts.db /app/backups/viral_shorts_$(date +\%Y\%m\%d_\%H\%M\%S).db

# Restart servizi se necessario ogni ora
0 * * * * /app/cloud_deployment/scripts/service_watchdog.sh
EOF

crontab /tmp/monitoring_cron

# Avvia cron daemon
cron

# Logging delle informazioni di avvio
log_success "All services started successfully!"

echo ""
echo "🎉 ViralShortsAI Cloud is now running!"
echo "=================================="
echo "📊 Services Status:"
echo "  🌐 Web Dashboard: http://localhost (port 80)"
echo "  🔌 API Server: http://localhost:8000"
echo "  📈 Monitoring: http://localhost:5555"
echo "  💾 Redis: localhost:6379"
echo ""
echo "📂 Important Paths:"
echo "  📄 Logs: /app/logs/"
echo "  💾 Data: /app/data/"
echo "  🔧 Config: /app/.env"
echo ""
echo "🛠️ Management Commands:"
echo "  📊 Health Check: /app/health_check.sh"
echo "  📄 View Logs: tail -f /app/logs/*.log"
echo "  🔄 Restart: docker-compose restart"
echo ""

# Monitora i processi principali e mantieni il container attivo
log_info "Starting process monitor..."

# Funzione per monitorare processi critici
monitor_processes() {
    while true; do
        # Controlla Gunicorn (Flask app)
        if ! pgrep -f "gunicorn.*web_app" > /dev/null; then
            log_warning "Flask app not running, restarting..."
            gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class gevent \
                     --daemon cloud_deployment.web_app:app
        fi
        
        # Controlla Celery Worker
        if ! pgrep -f "celery.*worker" > /dev/null; then
            log_warning "Celery worker not running, restarting..."
            celery -A cloud_deployment.celery_app worker --loglevel=info --detach
        fi
        
        # Controlla Nginx
        if ! pgrep nginx > /dev/null; then
            log_warning "Nginx not running, restarting..."
            nginx
        fi
        
        # Aspetta 30 secondi prima del prossimo controllo
        sleep 30
    done
}

# Avvia monitoring in background
monitor_processes &

# Mantieni il container attivo
log_info "Container is ready and monitoring processes..."
tail -f /app/logs/*.log
