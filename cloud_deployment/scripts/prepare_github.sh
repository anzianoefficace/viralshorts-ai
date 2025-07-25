#!/bin/bash

# 🚀 Script Deploy Automatico GitHub per ViralShortsAI
# Prepara il repository per deployment gratuito su cloud

set -e

echo "🚀 ViralShortsAI - Preparazione Deploy GitHub"
echo "=============================================="

# Colori
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

# Controlla se siamo nella directory corretta
if [ ! -f "main.py" ] || [ ! -f "daily_auto_poster.py" ]; then
    echo "❌ Errore: Esegui questo script dalla directory principale di ViralShortsAI"
    exit 1
fi

log_info "Directory corretta trovata ✅"

# Crea file .gitignore se non esiste
log_info "Creazione .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# App specific
data/downloads/*
data/processed/*
data/uploads/*
data/temp/*
logs/*.log
backups/
*.db
youtube_credentials.json

# Keep directory structure
!data/downloads/.gitkeep
!data/processed/.gitkeep
!data/uploads/.gitkeep
!data/temp/.gitkeep
!logs/.gitkeep
EOF

log_success ".gitignore creato"

# Crea directory structure markers
log_info "Creazione markers directory..."
mkdir -p data/{downloads,processed,uploads,reports,temp}
mkdir -p logs

touch data/downloads/.gitkeep
touch data/processed/.gitkeep  
touch data/uploads/.gitkeep
touch data/reports/.gitkeep
touch data/temp/.gitkeep
touch logs/.gitkeep

log_success "Directory structure preparata"

# Crea file requirements.txt se mancante
if [ ! -f "requirements.txt" ]; then
    log_info "Creazione requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core dependencies
PyQt5==5.15.9
apscheduler==3.11.0
openai==1.97.0
moviepy==1.0.3
matplotlib==3.10.3
pandas==2.3.1
schedule==1.2.0

# Database
sqlite3

# Utilities
requests==2.31.0
Pillow==10.0.0
EOF
    log_success "requirements.txt creato"
fi

# Crea Procfile per Heroku
log_info "Creazione Procfile per Heroku..."
cat > Procfile << 'EOF'
web: python cloud_deployment/render_app.py
worker: python -c "from daily_auto_poster import DailyAutoPoster; poster = DailyAutoPoster(); poster.start()"
EOF

log_success "Procfile creato"

# Crea runtime.txt per specificare versione Python
log_info "Creazione runtime.txt..."
echo "python-3.11.0" > runtime.txt
log_success "runtime.txt creato"

# Crea app.json per deploy 1-click
log_info "Creazione app.json per deploy automatico..."
cat > app.json << 'EOF'
{
  "name": "ViralShortsAI",
  "description": "AI-powered viral shorts automation platform",
  "repository": "https://github.com/YOUR_USERNAME/viralshorts-ai",
  "logo": "https://avatars.githubusercontent.com/u/1?s=200&v=4",
  "keywords": ["python", "ai", "youtube", "automation", "viral", "shorts"],
  "stack": "heroku-22",
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "env": {
    "OPENAI_API_KEY": {
      "description": "Your OpenAI API key for GPT integration",
      "required": true
    },
    "YOUTUBE_CLIENT_ID": {
      "description": "YouTube API Client ID",
      "required": true
    },
    "YOUTUBE_CLIENT_SECRET": {
      "description": "YouTube API Client Secret", 
      "required": true
    },
    "SECRET_KEY": {
      "description": "Flask secret key",
      "generator": "secret"
    }
  },
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    }
  },
  "addons": [
    {
      "plan": "heroku-postgresql:mini"
    },
    {
      "plan": "heroku-redis:mini"
    }
  ]
}
EOF

log_success "app.json creato"

# Crea README per deployment
log_info "Creazione README deployment..."
cat > DEPLOY_README.md << 'EOF'
# 🚀 ViralShortsAI Cloud Deployment

## Quick Deploy Buttons

### Render.com (Recommended)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Railway.app  
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Environment Variables Required

- `OPENAI_API_KEY`: Your OpenAI API key
- `YOUTUBE_CLIENT_ID`: YouTube API client ID  
- `YOUTUBE_CLIENT_SECRET`: YouTube API client secret

## Manual Setup

1. Fork this repository
2. Connect to your preferred platform
3. Set environment variables
4. Deploy!

The app will be available at your assigned URL and will start posting automatically.
EOF

log_success "DEPLOY_README.md creato"

# Inizializza git se non già fatto
if [ ! -d ".git" ]; then
    log_info "Inizializzazione repository Git..."
    git init
    log_success "Git repository inizializzato"
else
    log_info "Repository Git già esistente"
fi

# Aggiungi tutti i file
log_info "Aggiunta file al repository..."
git add .

# Commit iniziale
if git diff --staged --quiet; then
    log_warning "Nessun cambiamento da committare"
else
    log_info "Creazione commit..."
    git commit -m "🚀 Prepare for cloud deployment

- Add cloud deployment configuration
- Setup free hosting compatibility  
- Add environment configuration
- Optimize for Render, Railway, Heroku
- Include 1-click deploy buttons"
    
    log_success "Commit creato"
fi

# Mostra istruzioni finali
echo ""
echo "🎉 ================================================"
echo "🎉 REPOSITORY PRONTO PER DEPLOYMENT!"
echo "🎉 ================================================"
echo ""
log_info "📋 PROSSIMI PASSI:"
echo ""
echo "1️⃣  Push su GitHub:"
echo "   git remote add origin https://github.com/USERNAME/viralshorts-ai.git"
echo "   git push -u origin main"
echo ""
echo "2️⃣  Deploy su piattaforma gratuita:"
echo "   🥇 Render.com - https://render.com/deploy"
echo "   🚂 Railway.app - https://railway.app/new/template"  
echo "   📱 Heroku - https://heroku.com/deploy"
echo ""
echo "3️⃣  Configura Environment Variables:"
echo "   - OPENAI_API_KEY"
echo "   - YOUTUBE_CLIENT_ID"
echo "   - YOUTUBE_CLIENT_SECRET"
echo ""
echo "4️⃣  Enjoy! Il tuo ViralShortsAI sarà online 24/7! 🚀"
echo ""
log_success "Setup completato! Segui i passi sopra per il deploy."

# Crea script di verifica deployment
cat > verify_deployment.sh << 'EOF'
#!/bin/bash
# Script per verificare il deployment

echo "🔍 Verifica Deployment ViralShortsAI"
echo "==================================="

if [ -z "$1" ]; then
    echo "Usage: ./verify_deployment.sh <YOUR_APP_URL>"
    echo "Example: ./verify_deployment.sh https://viralshorts-abc123.onrender.com"
    exit 1
fi

URL=$1

echo "🌐 Testing app at: $URL"

# Test health endpoint
echo "🏥 Health check..."
if curl -f "$URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

# Test main dashboard  
echo "📊 Dashboard check..."
if curl -f "$URL" > /dev/null 2>&1; then
    echo "✅ Dashboard accessible"
else
    echo "❌ Dashboard not accessible"
fi

# Test API
echo "🔌 API check..."
if curl -f "$URL/api/status" > /dev/null 2>&1; then
    echo "✅ API responding"
else
    echo "❌ API not responding"
fi

echo ""
echo "🎉 Deployment verification complete!"
echo "📱 Access your app at: $URL"
EOF

chmod +x verify_deployment.sh
log_success "Script di verifica creato: ./verify_deployment.sh"

echo ""
log_success "🎊 Tutto pronto! Ora puoi deployare ViralShortsAI gratuitamente! 🎊"
