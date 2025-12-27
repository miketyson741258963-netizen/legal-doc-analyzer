# Deployment Guide for Legal Document Analyzer

This guide provides comprehensive instructions for deploying the Legal Document Analyzer application across multiple platforms and environments. Choose the deployment option that best fits your requirements.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment (EC2/RDS)](#aws-deployment-ec2rds)
5. [Heroku Deployment](#heroku-deployment)
6. [Google Cloud Deployment](#google-cloud-deployment)
7. [Azure Deployment](#azure-deployment)
8. [Security Hardening](#security-hardening)
9. [Troubleshooting](#troubleshooting)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 14.0+ (if frontend is included)
- **RAM**: Minimum 2GB for development, 4GB+ for production
- **Storage**: 10GB+ free space
- **Git**: Latest version

### Required Tools
- Docker and Docker Compose (for containerized deployments)
- AWS CLI (for AWS deployments)
- Heroku CLI (for Heroku deployment)
- Google Cloud SDK (for Google Cloud deployments)
- Azure CLI (for Azure deployments)
- PostgreSQL 12+ or MySQL 8+ (for database-backed deployments)

### Environment Variables
Ensure you have the following environment variables ready:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed domains
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` (for AWS deployments)
- `SENDGRID_API_KEY` or similar for email services
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git
cd legal-doc-analyzer
```

### Step 2: Create Virtual Environment

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-insecure-secret-key-for-development-only
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
LOG_LEVEL=DEBUG
```

### Step 5: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_documents.json
```

### Step 6: Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser. Admin interface available at `http://localhost:8000/admin`.

### Step 7: Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test document_analyzer

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Development Tools

```bash
# Code formatting with Black
black .

# Linting with Flake8
flake8 .

# Type checking with mypy
mypy .

# Security check with Bandit
bandit -r .
```

---

## Docker Deployment

### Step 1: Build Docker Image

Create a `Dockerfile` in the project root if not present:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### Step 2: Create Docker Compose File

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:13-alpine
    container_name: legal-doc-db
    environment:
      POSTGRES_DB: ${DB_NAME:-legal_docs}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    container_name: legal-doc-web
    command: >
      sh -c "python manage.py migrate &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      DEBUG: ${DEBUG:-False}
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-legal_docs}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS:-localhost,127.0.0.1}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: legal-doc-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Step 3: Create Environment File

Create `.env.docker`:

```env
DEBUG=False
SECRET_KEY=your-production-secret-key-here
DB_NAME=legal_docs
DB_USER=postgres
DB_PASSWORD=secure-password-here
ALLOWED_HOSTS=localhost,yourdomain.com
SENDGRID_API_KEY=your-sendgrid-key
LOG_LEVEL=INFO
```

### Step 4: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Stop services
docker-compose down
```

### Step 5: Docker Maintenance

```bash
# Remove unused images/volumes
docker system prune -a --volumes

# Backup database
docker-compose exec db pg_dump -U postgres legal_docs > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres legal_docs

# Update containers
docker-compose pull
docker-compose up -d
```

---

## AWS Deployment (EC2/RDS)

### Architecture Overview
- **EC2**: Application server (t3.medium or larger)
- **RDS**: PostgreSQL database (db.t3.micro or larger)
- **S3**: Static files and media storage
- **CloudFront**: CDN for static content
- **Route 53**: DNS management
- **Certificate Manager**: SSL/TLS certificates

### Step 1: Create RDS Database

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier legal-docs-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password "your-secure-password" \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxx \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted \
  --region us-east-1
```

### Step 2: Launch EC2 Instance

```bash
# Using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups legal-doc-analyzer \
  --subnet-id subnet-xxxxxxxx \
  --region us-east-1
```

Or use AWS Console:
1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Select Ubuntu 20.04 LTS AMI
4. Choose t3.medium instance type
5. Configure security groups to allow HTTP (80), HTTPS (443), SSH (22)
6. Launch and download key pair

### Step 3: Connect to EC2 Instance

```bash
chmod 400 your-key-pair.pem
ssh -i your-key-pair.pem ubuntu@your-ec2-public-ip
```

### Step 4: Install Dependencies on EC2

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and build tools
sudo apt-get install -y python3.10 python3-pip python3-venv \
  postgresql-client libpq-dev build-essential git

# Install Nginx
sudo apt-get install -y nginx

# Install Certbot for SSL
sudo apt-get install -y certbot python3-certbot-nginx

# Install Supervisor for process management
sudo apt-get install -y supervisor
```

### Step 5: Deploy Application

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git
sudo chown -R ubuntu:ubuntu legal-doc-analyzer
cd legal-doc-analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DATABASE_URL=postgresql://postgres:PASSWORD@your-rds-endpoint.rds.amazonaws.com:5432/legal_docs
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-key
LOG_LEVEL=INFO
EOF

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 6: Configure Gunicorn

Create `/var/www/legal-doc-analyzer/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
timeout = 30
graceful_timeout = 30
preload_app = True
```

### Step 7: Configure Supervisor

Create `/etc/supervisor/conf.d/legal-doc-analyzer.conf`:

```ini
[program:legal-doc-analyzer]
directory=/var/www/legal-doc-analyzer
command=/var/www/legal-doc-analyzer/venv/bin/gunicorn \
  -c gunicorn_config.py \
  config.wsgi:application
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/legal-doc-analyzer/gunicorn.log
environment=PATH="/var/www/legal-doc-analyzer/venv/bin"

[group:legal-doc-analyzer]
programs=legal-doc-analyzer
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start legal-doc-analyzer
```

### Step 8: Configure Nginx

Create `/etc/nginx/sites-available/legal-doc-analyzer`:

```nginx
upstream legal_doc_analyzer {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server block
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/legal-doc-analyzer-access.log;
    error_log /var/log/nginx/legal-doc-analyzer-error.log;

    # Client upload size
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;
    gzip_min_length 1000;
    gzip_disable "msie6";

    location / {
        proxy_pass http://legal_doc_analyzer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /var/www/legal-doc-analyzer/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/legal-doc-analyzer/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/legal-doc-analyzer \
  /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: Set Up SSL Certificate

```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Set up auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Step 10: Configure S3 for Static Files

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket legal-doc-analyzer-static \
  --region us-east-1

# Block public access
aws s3api put-public-access-block \
  --bucket legal-doc-analyzer-static \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Update Django settings
# In settings.py:
# AWS_STORAGE_BUCKET_NAME = 'legal-doc-analyzer-static'
# AWS_S3_REGION_NAME = 'us-east-1'
# STATIC_URL = 'https://legal-doc-analyzer-static.s3.amazonaws.com/'
```

### AWS Monitoring and Maintenance

```bash
# Check EC2 status
aws ec2 describe-instance-status --instance-id i-xxxxxxxx

# Monitor RDS
aws rds describe-db-instances --db-instance-identifier legal-docs-db

# Create backup
aws rds create-db-snapshot \
  --db-instance-identifier legal-docs-db \
  --db-snapshot-identifier legal-docs-backup-$(date +%Y%m%d)

# View CloudWatch logs
aws logs tail /aws/ec2/legal-doc-analyzer --follow
```

---

## Heroku Deployment

### Step 1: Create Heroku Account

1. Sign up at https://www.heroku.com
2. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
3. Login: `heroku login`

### Step 2: Create Heroku App

```bash
heroku create legal-doc-analyzer
```

Or if you already have the app:

```bash
heroku git:remote -a legal-doc-analyzer
```

### Step 3: Add PostgreSQL Database

```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0 -a legal-doc-analyzer

# Get database URL
heroku config:get DATABASE_URL -a legal-doc-analyzer
```

### Step 4: Create Procfile

Create `Procfile` in project root:

```
web: gunicorn config.wsgi
release: python manage.py migrate
worker: celery -A config worker -l info
```

### Step 5: Update requirements.txt

```bash
pip install gunicorn django-heroku
pip freeze > requirements.txt
```

### Step 6: Update Django Settings

Create `config/settings/heroku.py`:

```python
import dj_database_url
import django_heroku
from .base import *

# Use database from Heroku environment
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://localhost/legal_docs',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Allow Heroku hostname
ALLOWED_HOSTS = ['legal-doc-analyzer.herokuapp.com']

# Trust the x-forwarded-proto header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Force HTTPS
SECURE_SSL_REDIRECT = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Django Heroku configuration
django_heroku.settings(locals(), databases=False)
```

Update `config/settings/__init__.py` or `manage.py` to use Heroku settings in production.

### Step 7: Configure Environment Variables

```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
heroku config:set ALLOWED_HOSTS=legal-doc-analyzer.herokuapp.com
heroku config:set SENDGRID_API_KEY=your-sendgrid-key
heroku config:set AWS_STORAGE_BUCKET_NAME=your-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Step 8: Deploy to Heroku

```bash
# Add all changes to git
git add .
git commit -m "Configure for Heroku deployment"

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# View logs
heroku logs --tail
```

### Step 9: Custom Domain (Optional)

```bash
# Add custom domain
heroku domains:add your-domain.com

# Update DNS records with provided Heroku address
# Then in Heroku console:
heroku certs:auto:enable
```

### Heroku Maintenance

```bash
# Restart app
heroku restart

# Scale dynos
heroku ps:scale web=2

# View resource usage
heroku ps

# Database backups
heroku pg:backups:capture
heroku pg:backups:download

# Check app status
heroku status
```

---

## Google Cloud Deployment

### Step 1: Set Up Google Cloud Project

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

gcloud init
gcloud projects create legal-doc-analyzer
gcloud config set project legal-doc-analyzer
```

### Step 2: Create Cloud SQL Database

```bash
# Create PostgreSQL instance
gcloud sql instances create legal-docs-db \
  --database-version POSTGRES_13 \
  --tier db-f1-micro \
  --region us-central1 \
  --backup \
  --enable-bin-log

# Create database
gcloud sql databases create legal_docs \
  --instance legal-docs-db

# Create user
gcloud sql users create dbuser \
  --instance legal-docs-db \
  --password

# Get connection name
gcloud sql instances describe legal-docs-db \
  --format='value(connectionName)'
```

### Step 3: Create Compute Engine Instance

```bash
# Create VM instance
gcloud compute instances create legal-doc-analyzer \
  --image-family debian-11 \
  --image-project debian-cloud \
  --machine-type e2-medium \
  --zone us-central1-a \
  --scopes https://www.googleapis.com/auth/cloud-platform

# SSH into instance
gcloud compute ssh legal-doc-analyzer --zone us-central1-a
```

### Step 4: Install Dependencies on Compute Engine

```bash
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and tools
sudo apt-get install -y python3.10 python3-pip python3-venv \
  postgresql-client git nginx supervisor build-essential

# Install Google Cloud SQL proxy
curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 \
  -o cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/
```

### Step 5: Deploy Application

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git
sudo chown -R $(whoami):$(whoami) legal-doc-analyzer
cd legal-doc-analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DATABASE_URL=postgresql://dbuser:PASSWORD@127.0.0.1:5432/legal_docs
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
GCS_BUCKET_NAME=your-gcs-bucket
LOG_LEVEL=INFO
EOF

# Migrations
python manage.py migrate

# Superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 6: Configure Cloud SQL Proxy

Create `/etc/systemd/system/cloudsql-proxy.service`:

```ini
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloud_sql_proxy \
  -instances=PROJECT_ID:us-central1:legal-docs-db=127.0.0.1:5432
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cloudsql-proxy
sudo systemctl start cloudsql-proxy
```

### Step 7: Configure Supervisor and Nginx

(Similar to AWS section - use the same Supervisor and Nginx configurations)

### Step 8: Set Up Cloud Storage for Static Files

```bash
# Create storage bucket
gsutil mb gs://legal-doc-analyzer-static

# Set permissions
gsutil iam ch serviceAccount:YOUR-SERVICE-ACCOUNT@PROJECT_ID.iam.gserviceaccount.com:objectViewer \
  gs://legal-doc-analyzer-static

# Update Django settings to use GCS
# Install django-storages
pip install django-storages google-cloud-storage
```

Update `settings.py`:

```python
STORAGES = {
    'default': 'storages.backends.gcloud.GoogleCloudStorage',
    'staticfiles': 'storages.backends.gcloud.GoogleCloudStorage',
}
GCS_BUCKET_NAME = 'legal-doc-analyzer-static'
```

### Step 9: Set Up Cloud Load Balancer

```bash
# Create instance group
gcloud compute instance-groups managed create legal-doc-analyzer-group \
  --base-instance-name legal-doc-analyzer \
  --size 1 \
  --zone us-central1-a \
  --template legal-doc-analyzer

# Create health check
gcloud compute health-checks create http legal-doc-health-check \
  --request-path /health \
  --port 8000

# Create backend service
gcloud compute backend-services create legal-doc-backend \
  --protocol HTTP \
  --health-checks legal-doc-health-check \
  --global

# Add backend to service
gcloud compute backend-services add-backend legal-doc-backend \
  --instance-group legal-doc-analyzer-group \
  --zone us-central1-a \
  --global

# Create URL map
gcloud compute url-maps create legal-doc-lb \
  --default-service legal-doc-backend

# Create HTTP proxy
gcloud compute target-http-proxies create legal-doc-proxy \
  --url-map legal-doc-lb

# Create forwarding rule
gcloud compute forwarding-rules create legal-doc-forwarding-rule \
  --global \
  --target-http-proxy legal-doc-proxy \
  --address 0.0.0.0 \
  --ports 80
```

---

## Azure Deployment

### Step 1: Create Azure Account and Resources

```bash
# Install Azure CLI
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login
az login

# Create resource group
az group create \
  --name legal-doc-analyzer-rg \
  --location eastus
```

### Step 2: Create App Service

```bash
# Create App Service Plan
az appservice plan create \
  --name legal-doc-analyzer-plan \
  --resource-group legal-doc-analyzer-rg \
  --sku B2 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group legal-doc-analyzer-rg \
  --plan legal-doc-analyzer-plan \
  --name legal-doc-analyzer \
  --runtime "PYTHON|3.10"
```

### Step 3: Create Azure Database for PostgreSQL

```bash
# Create database server
az postgres server create \
  --resource-group legal-doc-analyzer-rg \
  --name legal-docs-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password Secure@Password123 \
  --sku-name B_Gen5_1 \
  --storage-size 51200 \
  --backup-retention 7 \
  --geo-redundant-backup Enabled \
  --ssl-enforcement Enabled

# Create database
az postgres db create \
  --resource-group legal-doc-analyzer-rg \
  --server-name legal-docs-db \
  --name legal_docs

# Create firewall rule for app
az postgres server firewall-rule create \
  --resource-group legal-doc-analyzer-rg \
  --server-name legal-docs-db \
  --name AllowAppService \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255
```

### Step 4: Create Storage Account

```bash
# Create storage account
az storage account create \
  --name legaldocstg \
  --resource-group legal-doc-analyzer-rg \
  --location eastus \
  --sku Standard_LRS

# Create blob container
az storage container create \
  --account-name legaldocstg \
  --name staticfiles

az storage container create \
  --account-name legaldocstg \
  --name media
```

### Step 5: Configure App Service

```bash
# Set Python version
az webapp config appsettings set \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --settings PYTHON_VERSION=3.10

# Configure startup command
az webapp config set \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --startup-file "gunicorn config.wsgi"

# Set environment variables
az webapp config appsettings set \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --settings \
  DEBUG=False \
  SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))') \
  DATABASE_URL="postgresql://dbadmin:PASSWORD@legal-docs-db.postgres.database.azure.com:5432/legal_docs?sslmode=require" \
  ALLOWED_HOSTS="legal-doc-analyzer.azurewebsites.net,your-domain.com" \
  AZURE_STORAGE_ACCOUNT_NAME=legaldocstg \
  AZURE_STORAGE_ACCOUNT_KEY=$(az storage account keys list --account-name legaldocstg --query [0].value -o tsv) \
  SENDGRID_API_KEY=your-sendgrid-key
```

### Step 6: Deploy Code

Create `.deployment` file:

```
[config]
command = deploy.sh
```

Create `deploy.sh`:

```bash
#!/bin/bash

set -e

# Activate virtual environment
source /home/site/wwwroot/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Copy static files to storage
python manage.py collectstatic --noinput \
  --settings=config.settings.azure
```

### Step 7: Deploy Using Git

```bash
# Configure deployment credentials
az webapp deployment user set --user-name yourname

# Get Git URL
az webapp deployment source config-local-git \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer

# Add remote
git remote add azure <GIT_URL_FROM_ABOVE>

# Deploy
git push azure main
```

Or deploy from GitHub:

```bash
# Connect GitHub repository
az webapp deployment source config \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --repo-url https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git \
  --branch main \
  --git-token YOUR_GITHUB_TOKEN
```

### Step 8: Set Up Custom Domain

```bash
# Add custom domain
az webapp config hostname add \
  --resource-group legal-doc-analyzer-rg \
  --webapp-name legal-doc-analyzer \
  --hostname your-domain.com

# Create SSL certificate
az webapp config ssl create \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --certificate-path path/to/certificate.pfx \
  --certificate-password your-password

# Bind SSL certificate
az webapp config ssl bind \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --certificate-thumbprint THUMBPRINT \
  --ssl-type SNI
```

### Step 9: Configure Monitoring

```bash
# Create Application Insights
az monitor app-insights component create \
  --app legal-doc-analyzer-insights \
  --location eastus \
  --resource-group legal-doc-analyzer-rg \
  --application-type web

# Link to App Service
az webapp config appsettings set \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$(az monitor app-insights component show \
    --app legal-doc-analyzer-insights \
    --resource-group legal-doc-analyzer-rg \
    --query instrumentationKey -o tsv)
```

---

## Security Hardening

### 1. Django Security Settings

Update `config/settings.py` with production security settings:

```python
# Security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
    'font-src': ["'self'", "fonts.googleapis.com"],
}

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Clickjacking protection
X_FRAME_OPTIONS = 'DENY'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# CORS settings (restrict to your domain)
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]

# Database connection security
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/legal-doc-analyzer.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}
```

### 2. Environment-Based Configuration

Create separate settings files:

```
config/settings/
├── __init__.py
├── base.py          # Shared settings
├── development.py   # Development-specific
├── production.py    # Production-specific
└── testing.py       # Testing-specific
```

### 3. Secrets Management

Use environment variables and secret managers:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name legal-doc-analyzer/db-password \
  --secret-string "your-secure-password"

# Azure Key Vault
az keyvault secret set \
  --vault-name legal-doc-secrets \
  --name db-password \
  --value "your-secure-password"

# Google Secret Manager
gcloud secrets create db-password \
  --replication-policy="automatic" \
  --data-file=-
```

### 4. Dependency Security

```bash
# Check for vulnerabilities
pip install safety bandit

# Scan dependencies
safety check

# Scan code for security issues
bandit -r .

# Keep dependencies updated
pip list --outdated
pip install --upgrade pip setuptools wheel
```

### 5. File Upload Security

```python
# settings.py
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Allowed document types
ALLOWED_DOCUMENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
]

# Virus scanning (with ClamAV)
# pip install pyclamd
import pyclamd
cv = pyclamd.ClamCI()
```

### 6. Firewall and Network Security

```bash
# AWS Security Group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0  # Restrict to your IP in production

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# GCP Firewall
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0

gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --source-ranges=0.0.0.0/0

gcloud compute firewall-rules create allow-ssh \
  --allow=tcp:22 \
  --source-ranges=YOUR_IP/32
```

### 7. Database Security

```bash
# PostgreSQL
# In pg_hba.conf, enforce SSL
hostssl    all             all             0.0.0.0/0               md5

# Create limited permission user
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE legal_docs TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

# Backup encryption
pg_dump legal_docs | gzip | openssl enc -aes-256-cbc > backup.sql.gz.enc
```

### 8. Regular Security Audits

```bash
# OWASP dependency check
pip install pip-audit
pip-audit

# Django security checks
python manage.py check --deploy

# Run security tests
python manage.py test --verbosity=2 -k security
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check database service status
sudo systemctl status postgresql  # Local PostgreSQL
heroku pg:info  # Heroku
aws rds describe-db-instances --db-instance-identifier legal-docs-db  # AWS

# Verify connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check firewall rules
# Ensure port 5432 is accessible
# Verify security group settings
```

#### 2. Static Files Not Loading

**Problem**: 404 errors for static files in production

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput --clear

# For S3/Cloud Storage
python manage.py collectstatic --noinput

# Check file permissions
ls -la staticfiles/

# Verify STATIC_ROOT and STATIC_URL settings
python manage.py shell -c "from django.conf import settings; print(settings.STATIC_ROOT)"

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Permission Denied Errors

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Fix directory ownership
sudo chown -R www-data:www-data /var/www/legal-doc-analyzer
sudo chown -R ubuntu:ubuntu /var/www/legal-doc-analyzer  # For ubuntu user

# Fix file permissions
chmod -R 755 /var/www/legal-doc-analyzer
chmod -R 644 /var/www/legal-doc-analyzer/static

# Check SELinux (if enabled)
getenforce
semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/legal-doc-analyzer(/.*)?"
restorecon -Rv /var/www/legal-doc-analyzer
```

#### 4. Out of Memory

**Problem**: Application crashes with `MemoryError` or server becomes unresponsive

**Solution**:
```bash
# Monitor memory usage
free -h
top -b -n 1 | head -20

# Configure Gunicorn workers
# Reduce workers if memory is limited
gunicorn config.wsgi --workers 2 --max-requests 1000

# Enable swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
/swapfile none swap sw 0 0

# Monitor and optimize queries
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as ctx:
...     # Your code here
>>> print(len(ctx))  # Number of queries
```

#### 5. Slow Application Performance

**Problem**: Page loads take more than expected

**Solution**:
```bash
# Enable query logging
# In settings.py
LOGGING = {
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Profile application
pip install django-silk
# Then analyze queries and performance

# Use caching
pip install django-redis
# Configure in settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Optimize database queries
# Use select_related() and prefetch_related()
# Add database indexes
# Use pagination

# Check server resources
vmstat 1 5
iostat -x 1 5
```

#### 6. Certificate Issues

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED` or mixed content warnings

**Solution**:
```bash
# Check certificate validity
openssl s_client -connect your-domain.com:443

# Renew SSL certificate
sudo certbot renew --dry-run
sudo certbot renew

# Fix mixed content (ensure all resources are HTTPS)
# In templates and static files, use https://
# Or use protocol-relative URLs: //cdn.example.com/script.js

# Update SECURE_SSL_REDIRECT settings
SECURE_SSL_REDIRECT = True
```

#### 7. Celery Task Issues

**Problem**: Tasks not executing or queuing up

**Solution**:
```bash
# Check Celery worker status
celery -A config inspect active

# Check task queue
celery -A config inspect reserved

# Clear task queue
celery -A config purge

# Monitor Celery
celery -A config events

# Restart worker
sudo supervisorctl restart celery

# Check logs
tail -f /var/log/celery/worker.log
```

#### 8. Email Issues

**Problem**: Emails not being sent

**Solution**:
```bash
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])

# Check email settings
python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"

# Verify SMTP credentials
# Ensure SendGrid/email service API keys are correct

# Check Nginx logs
tail -f /var/log/nginx/error.log

# Verify firewall allows outbound SMTP
telnet smtp.sendgrid.net 587
```

#### 9. Docker Issues

**Problem**: Containers not starting or exiting

**Solution**:
```bash
# Check container logs
docker logs container_name

# View detailed error
docker-compose logs -f web

# Inspect container
docker inspect container_name

# Rebuild image
docker-compose build --no-cache

# Remove dangling containers
docker container prune

# Check disk space
docker system df

# Restart services
docker-compose restart
```

#### 10. Deployment Failures

**Problem**: Git push or deployment fails

**Solution**:
```bash
# Check Git status
git status
git log --oneline

# Verify deployment logs
# Heroku
heroku logs --tail

# AWS CloudFormation
aws cloudformation describe-stack-events --stack-name legal-doc-analyzer

# Azure
az webapp deployment slot list \
  --resource-group legal-doc-analyzer-rg \
  --name legal-doc-analyzer

# GCP App Engine
gcloud app logs read -v

# Check file permissions
ls -la /path/to/project

# Ensure all dependencies are in requirements.txt
pip freeze | grep -v egg > requirements.txt
```

### Debugging Commands

```bash
# Django debug toolbar (development only)
pip install django-debug-toolbar

# Check for errors
python manage.py check --deploy

# Validate settings
python manage.py shell -c "from django.conf import settings; print('Settings loaded successfully')"

# Database connection test
python manage.py dbshell

# Check installed apps
python manage.py shell -c "from django.apps import apps; print(apps.get_app_configs())"

# View running processes
ps aux | grep python
ps aux | grep gunicorn

# Check open ports
netstat -tuln | grep LISTEN
ss -tuln | grep LISTEN

# Monitor system resources
htop
free -h
df -h
du -sh /path/to/directory
```

---

## Monitoring and Maintenance

### 1. Health Checks

Create a health check endpoint:

```python
# In urls.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def health_check(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

### 2. Backup Strategy

```bash
# Daily backups
0 2 * * * pg_dump legal_docs | gzip > /backups/legal_docs_$(date +\%Y\%m\%d).sql.gz

# Verify backup
gzip -t /backups/legal_docs_*.sql.gz

# Upload to cloud storage
0 3 * * * aws s3 cp /backups/ s3://backup-bucket/daily/ --recursive

# Retention policy
find /backups -name "legal_docs_*.sql.gz" -mtime +30 -delete
```

### 3. Log Management

```bash
# Rotate logs
cat > /etc/logrotate.d/legal-doc-analyzer << EOF
/var/log/legal-doc-analyzer/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload legal-doc-analyzer > /dev/null 2>&1 || true
    endscript
}
EOF

# Monitor logs
tail -f /var/log/django/legal-doc-analyzer.log
tail -f /var/log/nginx/legal-doc-analyzer-error.log
```

### 4. Automated Updates

```bash
# Enable unattended updates
sudo apt-get install -y unattended-upgrades

# Configure
cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
EOF

# Enable
systemctl enable unattended-upgrades
systemctl start unattended-upgrades
```

### 5. Performance Monitoring

```python
# Install monitoring tools
pip install django-prometheus

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'django_prometheus',
]

# Add middleware
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# URLs
urlpatterns = [
    path('metrics/', include('django_prometheus.urls')),
]
```

### 6. Security Updates

```bash
# Check for security vulnerabilities
pip-audit

# Update packages
pip list --outdated
pip install --upgrade package-name

# Check system updates
apt list --upgradable

# Apply updates
sudo apt-get update
sudo apt-get upgrade

# Schedule automated security updates
sudo apt-get install -y apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Additional Resources

- [Django Deployment Documentation](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [12 Factor App](https://12factor.net/)
- [OWASP Security Guidelines](https://owasp.org/)
- [Cloud Provider Documentation](#)
  - [AWS Deployment](https://docs.aws.amazon.com/)
  - [Heroku Deployment](https://devcenter.heroku.com/)
  - [Google Cloud](https://cloud.google.com/docs/)
  - [Azure](https://docs.microsoft.com/en-us/azure/)

## Support and Contribution

For issues, questions, or contributions, please:

1. Check existing [GitHub Issues](https://github.com/miketyson741258963-netizen/legal-doc-analyzer/issues)
2. Create a new issue with detailed information
3. Submit pull requests with improvements

---

**Last Updated**: 2025-12-27
**Version**: 1.0.0

For the latest information, visit: [GitHub Repository](https://github.com/miketyson741258963-netizen/legal-doc-analyzer)
