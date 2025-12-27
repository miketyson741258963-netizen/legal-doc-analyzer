# Legal Doc Analyzer

A comprehensive legal document analysis and processing system designed to extract, parse, and analyze legal documents with advanced NLP capabilities.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [Deployment Guide](#deployment-guide)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Overview

Legal Doc Analyzer is a powerful tool for professionals who need to process, analyze, and extract insights from legal documents. The system leverages modern natural language processing (NLP) techniques to automatically identify key sections, extract relevant information, and provide actionable insights from complex legal documents.

### Key Use Cases

- Contract analysis and clause extraction
- Document classification and tagging
- Risk identification in legal agreements
- Key party and date extraction
- Document summarization
- Compliance checking

## Features

### Core Capabilities

- **Document Upload & Processing**: Support for multiple file formats (PDF, DOCX, TXT)
- **Intelligent Text Extraction**: Advanced OCR and text parsing for scanned documents
- **Key Information Extraction**: Automatically identifies parties, dates, obligations, and important clauses
- **Document Classification**: Categorizes documents by type (contracts, agreements, policies, etc.)
- **Risk Assessment**: Flags potential risks and unusual clauses
- **Full-Text Search**: Index and search across all processed documents
- **Batch Processing**: Handle multiple documents simultaneously
- **API Integration**: RESTful API for seamless third-party integration
- **User Management**: Role-based access control (RBAC)
- **Audit Logging**: Complete tracking of all operations

### Advanced Features

- Machine learning models for improved accuracy
- Custom template support for domain-specific analysis
- Comparison tool for contract analysis
- Export to multiple formats (JSON, CSV, PDF)
- Real-time processing with webhooks
- Document version control and history

## Project Structure

```
legal-doc-analyzer/
├── src/
│   ├── api/                    # REST API endpoints
│   ├── services/               # Business logic
│   ├── models/                 # Data models and schemas
│   ├── utils/                  # Utility functions
│   ├── extractors/             # Document extraction modules
│   └── ml/                     # Machine learning models
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── config/
│   ├── settings.py             # Configuration settings
│   └── logging.yml             # Logging configuration
├── docs/
│   ├── api.md                  # API documentation
│   ├── deployment.md           # Deployment guide
│   └── architecture.md         # Architecture overview
├── docker/
│   ├── Dockerfile              # Docker image definition
│   └── docker-compose.yml      # Multi-container setup
├── scripts/
│   ├── setup.sh                # Setup script
│   └── migrate.py              # Database migrations
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── README.md                   # This file
└── LICENSE                     # License information
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager
- PostgreSQL 12 or higher
- Redis 6.0 or higher (optional, for caching)
- Docker & Docker Compose (for containerized setup)

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git
   cd legal-doc-analyzer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize Database**
   ```bash
   python scripts/migrate.py
   ```

6. **Create Superuser (Optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000`

### Docker Setup

1. **Build Docker Image**
   ```bash
   docker build -t legal-doc-analyzer:latest ./docker
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Check Logs**
   ```bash
   docker-compose logs -f web
   ```

### Installing Optional Dependencies

For additional features, install optional packages:

```bash
# For GPU support
pip install torch[cuda]

# For advanced NLP models
pip install transformers sentencepiece

# For development
pip install pytest pytest-cov black flake8 mypy
```

## Usage Guide

### API Quick Start

#### Upload a Document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

#### Analyze a Document
```bash
curl -X POST http://localhost:8000/api/documents/{doc_id}/analyze \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Retrieve Analysis Results
```bash
curl -X GET http://localhost:8000/api/documents/{doc_id}/analysis \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Web Interface

1. Navigate to `http://localhost:8000` in your browser
2. Log in with your credentials
3. Upload documents via the intuitive dashboard
4. View analysis results and extracted information
5. Export results in your preferred format

## Deployment Guide

### Prerequisites for Production

- A Linux-based server (Ubuntu 20.04 LTS recommended)
- PostgreSQL instance
- Redis instance (optional)
- SSL/TLS certificates
- Domain name
- Adequate storage for document storage (minimum 100GB recommended)

### Step 1: Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3.9 python3-pip python3-venv \
  postgresql postgresql-contrib redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash appuser
sudo su - appuser
```

### Step 2: Application Deployment

```bash
# Clone repository
git clone https://github.com/miketyson741258963-netizen/legal-doc-analyzer.git
cd legal-doc-analyzer

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with production settings
cp .env.example .env
nano .env  # Configure production variables
```

### Step 3: Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb legal_doc_analyzer
sudo -u postgres createuser -P app_user  # Set a strong password

# Run migrations
python scripts/migrate.py
```

### Step 4: Web Server Configuration (Nginx)

Create `/etc/nginx/sites-available/legal-doc-analyzer`:

```nginx
upstream legal_doc_analyzer {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://legal_doc_analyzer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/legal-doc-analyzer/static/;
    }
    
    location /media/ {
        alias /var/www/legal-doc-analyzer/media/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/legal-doc-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Systemd Service Setup

Create `/etc/systemd/system/legal-doc-analyzer.service`:

```ini
[Unit]
Description=Legal Doc Analyzer Application
After=network.target postgresql.service

[Service]
Type=notify
User=appuser
WorkingDirectory=/home/appuser/legal-doc-analyzer
Environment="PATH=/home/appuser/legal-doc-analyzer/venv/bin"
ExecStart=/home/appuser/legal-doc-analyzer/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/legal-doc-analyzer/access.log \
    --error-logfile /var/log/legal-doc-analyzer/error.log \
    wsgi:application

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable legal-doc-analyzer
sudo systemctl start legal-doc-analyzer
```

### Step 6: SSL/TLS Configuration

Using Let's Encrypt (free):
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

### Step 7: Monitoring and Logging

```bash
# Create log directory
sudo mkdir -p /var/log/legal-doc-analyzer
sudo chown appuser:appuser /var/log/legal-doc-analyzer

# View logs
sudo journalctl -u legal-doc-analyzer -f
```

### Step 8: Backup Configuration

Create a backup script at `/home/appuser/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/legal-doc-analyzer"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Backup database
pg_dump legal_doc_analyzer > $BACKUP_DIR/db_$TIMESTAMP.sql

# Backup documents
tar -czf $BACKUP_DIR/documents_$TIMESTAMP.tar.gz /var/www/legal-doc-analyzer/media/

# Keep only 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

Schedule with crontab:
```bash
0 2 * * * /home/appuser/backup.sh
```

## Configuration

### Environment Variables

Key environment variables for configuration:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/legal_doc_analyzer

# AWS S3 (for document storage)
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Application
LOG_LEVEL=INFO
WORKERS=4
```

## API Reference

### Authentication

All API endpoints require authentication via Bearer token:

```bash
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Main Endpoints

- `POST /api/documents/upload` - Upload a new document
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}/` - Get document details
- `POST /api/documents/{id}/analyze` - Analyze a document
- `GET /api/documents/{id}/analysis` - Get analysis results
- `DELETE /api/documents/{id}/` - Delete a document
- `POST /api/documents/{id}/export` - Export document analysis

See `docs/api.md` for complete API documentation.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

```bash
# Run tests
pytest tests/

# Check code quality
flake8 src/
black src/

# Type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:

1. Check the [documentation](docs/)
2. Open an issue on GitHub
3. Contact: support@your-domain.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Last Updated**: 2025-12-27
**Version**: 1.0.0
