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
