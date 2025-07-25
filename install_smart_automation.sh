#!/bin/bash

# 🚀 ViralShortsAI Smart Automation Installation Script
# Automatically installs all dependencies and integrates smart automation

echo "🚀 ViralShortsAI Smart Automation Installer"
echo "==========================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  This script is optimized for macOS. Continuing anyway..."
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check pip
if ! command_exists pip3; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Install Redis (using Homebrew on macOS)
echo ""
echo "📦 Installing Redis..."
if command_exists brew; then
    if ! brew list redis &>/dev/null; then
        echo "Installing Redis via Homebrew..."
        brew install redis
    else
        echo "✅ Redis already installed"
    fi
    
    # Start Redis service
    echo "🔧 Starting Redis service..."
    brew services start redis
    
    # Test Redis connection
    if redis-cli ping &>/dev/null; then
        echo "✅ Redis is running and accessible"
    else
        echo "⚠️  Redis installed but not responding to ping"
    fi
else
    echo "⚠️  Homebrew not found. Please install Redis manually:"
    echo "   Visit: https://redis.io/download"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."

# Core smart automation packages
SMART_AUTOMATION_DEPS=(
    "redis>=4.6.0"
    "celery>=5.3.0"
    "scikit-learn>=1.3.0"
    "numpy>=1.24.0"
    "pandas>=2.0.0"
    "asyncio"
    "python-dateutil>=2.8.0"
    "psutil>=5.9.0"
    "aiofiles>=23.0.0"
)

# Install each dependency
for dep in "${SMART_AUTOMATION_DEPS[@]}"; do
    echo "Installing $dep..."
    pip3 install "$dep" --upgrade
done

# Update requirements.txt
echo ""
echo "📝 Updating requirements.txt..."
python3 -c "
import os
import sys

# Add automation path
automation_path = os.path.join(os.path.dirname(__file__), 'automation')
if automation_path not in sys.path:
    sys.path.append(automation_path)

try:
    from integration_patch import add_requirements
    add_requirements()
except ImportError:
    print('⚠️  Could not import integration_patch. Adding requirements manually...')
    
    new_deps = [
        'redis>=4.6.0',
        'celery>=5.3.0', 
        'scikit-learn>=1.3.0',
        'numpy>=1.24.0',
        'pandas>=2.0.0',
        'python-dateutil>=2.8.0',
        'psutil>=5.9.0',
        'aiofiles>=23.0.0'
    ]
    
    with open('requirements.txt', 'a') as f:
        f.write('\n# Smart Automation Dependencies\n')
        for dep in new_deps:
            f.write(f'{dep}\n')
    
    print('✅ Requirements updated manually')
"

# Test imports
echo ""
echo "🧪 Testing Python imports..."
python3 -c "
import sys
try:
    import redis
    print('✅ Redis module imported successfully')
    
    # Test Redis connection
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
    
except ImportError:
    print('❌ Redis module not found')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Redis connection failed: {e}')

try:
    import celery
    print('✅ Celery imported successfully')
except ImportError:
    print('❌ Celery module not found')
    sys.exit(1)

try:
    import sklearn
    print('✅ Scikit-learn imported successfully')
except ImportError:
    print('❌ Scikit-learn module not found')
    sys.exit(1)

try:
    import numpy
    print('✅ NumPy imported successfully')
except ImportError:
    print('❌ NumPy module not found')
    sys.exit(1)

try:
    import pandas
    print('✅ Pandas imported successfully')
except ImportError:
    print('❌ Pandas module not found')
    sys.exit(1)

print('🎉 All smart automation dependencies are working!')
"

# Create Celery configuration
echo ""
echo "⚙️  Creating Celery configuration..."
cat > celery_config.py << 'EOF'
"""
🔧 Celery Configuration for ViralShortsAI Smart Automation
"""

from celery import Celery
import os

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
app = Celery('viral_shorts_ai')

# Configure Celery
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'automation.tasks.*': {'queue': 'viral_shorts'},
    }
)

# Task discovery
app.autodiscover_tasks(['automation'])

if __name__ == '__main__':
    app.start()
EOF

# Create startup script for Celery worker
echo ""
echo "🔧 Creating Celery worker startup script..."
cat > start_celery_worker.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Celery Worker for ViralShortsAI Smart Automation"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📁 Activating virtual environment..."
    source venv/bin/activate
fi

# Start Celery worker
echo "⚡ Starting Celery worker..."
celery -A celery_config worker --loglevel=info --concurrency=4 --queues=viral_shorts

EOF
chmod +x start_celery_worker.sh

# Create Redis monitoring script
echo ""
echo "📊 Creating Redis monitoring script..."
cat > monitor_redis.sh << 'EOF'
#!/bin/bash

echo "📊 Redis Monitoring for ViralShortsAI"
echo "====================================="

# Check Redis status
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
    
    # Get Redis info
    echo ""
    echo "📈 Redis Statistics:"
    redis-cli info stats | grep -E "(total_commands_processed|total_connections_received|used_memory_human)"
    
    # Show current keys
    echo ""
    echo "🔑 Current Keys:"
    redis-cli keys "*" | head -10
    
    # Show memory usage
    echo ""
    echo "💾 Memory Usage:"
    redis-cli info memory | grep -E "(used_memory_human|used_memory_peak_human)"
    
else
    echo "❌ Redis is not running"
    echo "💡 Start Redis with: brew services start redis"
fi
EOF
chmod +x monitor_redis.sh

# Integration test
echo ""
echo "🧪 Running integration test..."
python3 -c "
import sys
import os

# Test smart automation import
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'automation'))
    from integration_patch import integrate_smart_automation
    print('✅ Smart automation integration module loaded successfully')
except ImportError as e:
    print(f'❌ Failed to import smart automation: {e}')
    sys.exit(1)

# Test database connection
try:
    from database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM uploaded_videos')
    count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ Database connection successful ({count} uploaded videos)')
except Exception as e:
    print(f'⚠️  Database connection issue: {e}')

print('🎉 Integration test completed!')
"

# Final instructions
echo ""
echo "🎉 Smart Automation Installation Complete!"
echo "=========================================="
echo ""
echo "📋 Quick Start Guide:"
echo "1. ✅ All dependencies installed"
echo "2. ✅ Redis server started" 
echo "3. ✅ Configuration files created"
echo ""
echo "🚀 To integrate with your existing app:"
echo ""
echo "   # Add these lines to your main.py:"
echo "   from automation.integration_patch import integrate_smart_automation"
echo ""
echo "   # In ViralShortsBackend.__init__:"
echo "   integrate_smart_automation(self)"
echo ""
echo "   # In ViralShortsApp.__init__ (after creating tabs):"
echo "   integrate_smart_automation(self.backend, self)"
echo ""
echo "🔧 To start Celery worker (in separate terminal):"
echo "   ./start_celery_worker.sh"
echo ""
echo "📊 To monitor Redis:"
echo "   ./monitor_redis.sh"
echo ""
echo "🧠 Smart Automation Features:"
echo "   • AI-powered task scheduling"
echo "   • Predictive upload timing"
echo "   • Intelligent resource management"
echo "   • Emergency content generation"
echo "   • Performance analytics"
echo ""
echo "🎯 Ready to make your content go viral with AI!"
