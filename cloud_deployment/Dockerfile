# 🐳 Production Dockerfile for ViralShortsAI Cloud
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    imagemagick \
    curl \
    wget \
    git \
    cron \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy for security
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
COPY cloud_requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r cloud_requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/data/downloads \
             /app/data/processed \
             /app/data/uploads \
             /app/data/reports \
             /app/data/temp \
             /app/logs \
             /app/static \
             /app/templates

# Copy configuration files
COPY cloud_deployment/config/supervisor.conf /etc/supervisor/conf.d/
COPY cloud_deployment/config/nginx.conf /etc/nginx/sites-available/default
COPY cloud_deployment/config/crontab /etc/cron.d/viralshorts

# Set permissions
RUN chmod 0644 /etc/cron.d/viralshorts
RUN chmod +x /app/cloud_deployment/scripts/*.sh

# Create non-root user for security
RUN useradd -m -u 1000 viralshorts && \
    chown -R viralshorts:viralshorts /app && \
    chown viralshorts:viralshorts /var/log/nginx

# Expose ports
EXPOSE 80 8000 5555

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start services
CMD ["/app/cloud_deployment/scripts/start_services.sh"]
