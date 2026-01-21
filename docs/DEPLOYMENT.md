# CEP Proprietary Machine Deployment Guide

## Overview

This guide covers deploying the CEP Proprietary Machine in various environments, from local development to production.

## Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional)
- 4GB RAM minimum
- 10GB disk space

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/stackconsult/myMachine.git
cd myMachine
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required for LLM features
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional for enhanced search
FIRECRAWL_API_KEY=your_firecrawl_key_here

# Database
DATABASE_URL=./data/cep_machine.db

# Cache (Redis/Dragonfly)
CACHE_HOST=localhost:6379
```

### 5. Initialize Local Services

```bash
# Install Ollama for local LLM
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2

# Install Playwright browsers
playwright install chromium
```

### 6. Initialize Database

```bash
python -c "
import asyncio
from cep_machine.core.database import Database
asyncio.run(Database().initialize())
print('Database initialized')
"
```

## Deployment Options

### Option 1: Local Development

Run directly on your machine:

```bash
# Run individual layer
python -m cep_machine.layers.prospector

# Run with configuration
python -m cep_machine.main --config config.yaml

# Run in debug mode
python -m cep_machine.main --debug --layer=1
```

### Option 2: Docker Deployment

Build and run with Docker:

```bash
# Build image
docker build -t cep-machine .

# Run container
docker run -d \
  --name cep-machine \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  cep-machine
```

Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN playwright install chromium
RUN playwright install-deps

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data

# Initialize database
RUN python -c "
import asyncio
from cep_machine.core.database import Database
asyncio.run(Database().initialize())
"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "cep_machine.main"]
```

### Option 3: Docker Compose

For full stack with database and cache:

```yaml
# docker-compose.yml
version: '3.8'

services:
  cep-machine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/cep
      - CACHE_HOST=redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=cep
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Run with:
```bash
docker-compose up -d
```

### Option 4: Cloud Deployment

#### Heroku

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create cep-machine

# Set environment variables
heroku config:set OPENAI_API_KEY=$OPENAI_API_KEY
heroku config:set ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Deploy
git push heroku main
```

#### AWS EC2

1. Launch EC2 instance (t3.medium recommended)
2. Install Docker:
```bash
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
```
3. Deploy with Docker Compose

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/cep-machine

# Deploy
gcloud run deploy cep-machine \
  --image gcr.io/PROJECT_ID/cep-machine \
  --platform managed \
  --region us-central1
```

## Configuration

### Production Config

Create `config.prod.yaml`:

```yaml
cep:
  environment: production
  debug: false
  log_level: INFO

database:
  url: ${DATABASE_URL}
  pool_size: 20
  max_overflow: 30

cache:
  host: ${CACHE_HOST}
  port: 6379
  db: 0

security:
  webhook_secret: ${WEBHOOK_SECRET}
  jwt_secret: ${JWT_SECRET}

performance:
  worker_processes: 4
  max_connections: 1000
  timeout: 30
```

### Environment-Specific Settings

| Setting | Development | Production |
|---------|-------------|------------|
| Debug | True | False |
| Log Level | DEBUG | INFO |
| Database | SQLite | PostgreSQL |
| Cache | None | Redis |
| Workers | 1 | 4+ |
| SSL | No | Yes |

## Monitoring

### Health Checks

```bash
# Check system health
curl http://localhost:8000/health

# Check Φ_sync
curl http://localhost:8000/api/coherence
```

### Logs

```bash
# View logs
docker logs cep-machine

# Follow logs
docker logs -f cep-machine

# Filter logs
docker logs cep-machine | grep ERROR
```

### Metrics

Prometheus metrics available at `/metrics`:

- `cep_phi_sync`: Current coherence score
- `cep_layer_duration`: Layer execution time
- `cep_container_health`: Container health scores
- `cep_api_requests`: API request count

## Security

### 1. API Keys

- Never commit API keys to repository
- Use environment variables
- Rotate keys regularly
- Use key management service in production

### 2. Webhooks

```python
# Verify webhook signatures
from cep_machine.layers.booking_handler import BookingHandler

handler = BookingHandler(
    calendly_signing_key=os.getenv("CALENDLY_SIGNING_KEY")
)
```

### 3. Network Security

- Use HTTPS in production
- Implement rate limiting
- Add authentication headers
- Configure firewall rules

## Scaling

### Horizontal Scaling

1. Load balancer configuration
2. Shared database
3. Distributed cache
4. Session affinity

### Vertical Scaling

1. Increase CPU cores
2. Add more RAM
3. Use SSD storage
4. Optimize queries

## Backup and Recovery

### Database Backup

```bash
# SQLite
cp data/cep_machine.db data/backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump cep > backup_$(date +%Y%m%d).sql
```

### Automated Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

# Backup database
cp data/cep_machine.db backups/cep_${DATE}.db

# Backup config
cp config.yaml backups/config_${DATE}.yaml

# Cleanup old backups (keep 30 days)
find backups -name "*.db" -mtime +30 -delete
find backups -name "*.yaml" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

## Troubleshooting

### Common Issues

1. **Port already in use**
```bash
lsof -i :8000
kill -9 PID
```

2. **Database locked**
```bash
rm data/cep_machine.db-journal
```

3. **Out of memory**
```bash
# Increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

4. **API rate limits**
```bash
# Check usage logs
grep "rate limit" logs/cep.log
```

### Performance Tuning

1. **Database optimization**
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

2. **Connection pooling**
```python
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30
}
```

3. **Async optimization**
```python
# Use semaphore for concurrency
semaphore = asyncio.Semaphore(10)
```

## Maintenance

### Daily Tasks

- Check system health
- Review error logs
- Monitor Φ_sync trends
- Verify backups

### Weekly Tasks

- Update dependencies
- Rotate API keys
- Clean up old data
- Performance review

### Monthly Tasks

- Security audit
- Capacity planning
- Cost optimization
- Documentation update

---

*Deploy with confidence. Monitor for success.*
