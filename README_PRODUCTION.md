# CEP Machine - Production Deployment Guide

## Overview
This guide covers the complete production setup for CEP Machine with CopilotKit Agentic Chat UI, including advanced agent frameworks, monitoring, and security.

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Agent Layer   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (LangGraph)   │
│                 │    │                 │    │                 │
│ • Agentic Chat  │    │ • CopilotKit    │    │ • Business      │
│ • Advanced UI   │    │   Runtime       │    │   Agents        │
│ • Tool Execution│    │ • Tool API      │    │ • Tool Execution│
│ • Real-time     │    │ • Agent Mgmt    │    │ • State Mgmt    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ available space
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for production)

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd myMachine
```

### 2. Environment Configuration
```bash
# Copy production environment template
cp .env.production .env

# Edit environment variables
nano .env
```

**Critical Security Settings:**
```bash
# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Update in .env file
```

### 3. Deploy
```bash
# Run deployment script
./deploy.sh
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **Kibana**: http://localhost:5601

## Configuration

### Environment Variables

#### Core Application
```bash
NODE_ENV=production
PYTHON_ENV=production
LOG_LEVEL=INFO
```

#### CopilotKit
```bash
COPILOTKIT_LICENSE_KEY=ck_pub_your_license_key
COPILOTKIT_RUNTIME_URL=/api/copilotkit
COPILOTKIT_AGENT_NAME=cep_machine
```

#### Database
```bash
DATABASE_URL=postgresql://user:password@postgres:5432/cep_machine
REDIS_URL=redis://redis:6379/0
```

#### Security
```bash
SECRET_KEY=your-super-secret-key-256-bits-minimum
JWT_SECRET_KEY=your-jwt-secret-key-256-bits-minimum
ENCRYPTION_KEY=your-encryption-key-32-chars-minimum
```

#### External APIs
```bash
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
FIRECRAWL_API_KEY=your-firecrawl-api-key
```

## Services

### Frontend (Next.js)
- **Port**: 3000
- **Features**: Agentic Chat UI, Advanced Components
- **Health Check**: http://localhost:3000

### Backend (FastAPI)
- **Port**: 8000
- **Features**: CopilotKit Runtime, Tool Execution, Agent Management
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Database (PostgreSQL)
- **Port**: 5432
- **Purpose**: Persistent data storage
- **Backup**: Automated daily backups

### Cache (Redis)
- **Port**: 6379
- **Purpose**: Caching, session management

### Monitoring
- **Prometheus**: http://localhost:9090 (Metrics collection)
- **Grafana**: http://localhost:3001 (Visualization)
- **Elasticsearch**: http://localhost:9200 (Log storage)
- **Kibana**: http://localhost:5601 (Log analysis)

## Advanced Features

### 1. Agentic Chat UI
The advanced chat interface includes:
- **Multi-Agent Support**: Business Growth, Performance Analysis, Finance Tracking
- **Tool Execution**: Real-time tool invocation with progress tracking
- **Context Management**: Persistent conversation state
- **Custom Rendering**: Tailored message types and UI components

### 2. Agent Framework
LangGraph-based agents with:
- **State Management**: Complex workflow orchestration
- **Tool Integration**: 5+ specialized tools
- **Error Handling**: Robust error recovery
- **Performance Tracking**: Execution metrics

### 3. Tool Execution API
Production-ready tool execution:
- **Async Processing**: Background task execution
- **Rate Limiting**: Prevents abuse
- **Timeout Management**: Configurable timeouts
- **Error Logging**: Comprehensive error tracking

### 4. Security
Enterprise-grade security:
- **JWT Authentication**: Secure token-based auth
- **Rate Limiting**: API protection
- **Input Sanitization**: XSS prevention
- **Data Encryption**: Sensitive data protection

## Monitoring & Observability

### Metrics Collected
- **Application Metrics**: Request count, duration, error rate
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Tool executions, agent invocations
- **Custom Metrics**: Application-specific KPIs

### Grafana Dashboards
Pre-configured dashboards for:
- **Application Performance**
- **System Health**
- **Business Analytics**
- **Security Events**

### Log Management
- **Structured Logging**: JSON format
- **Log Rotation**: Daily rotation with retention
- **Centralized Collection**: Elasticsearch aggregation
- **Search & Analysis**: Kibana interface

## Deployment Operations

### Starting Services
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Stopping Services
```bash
docker-compose -f docker-compose.production.yml down
```

### Viewing Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
```

### Backup & Restore
```bash
# Backup data volumes
./deploy.sh backup

# Manual backup
docker run --rm -v cep-machine_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Updates
```bash
# Pull latest code
git pull origin main

# Redeploy
./deploy.sh
```

## Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs

# Check resource usage
docker stats

# Check disk space
df -h
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# Check connection string
docker-compose -f docker-compose.production.yml exec backend python -c "from database import engine; print(engine.url)"
```

#### 3. High Memory Usage
```bash
# Check container memory
docker stats --no-stream

# Restart services
docker-compose -f docker-compose.production.yml restart
```

#### 4. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Generate new certificates (if needed)
./scripts/generate-ssl-cert.sh
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_tools_status ON tools(status);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM messages WHERE created_at > NOW() - INTERVAL '1 day';
```

#### 2. Redis Optimization
```bash
# Check Redis memory usage
docker-compose -f docker-compose.production.yml exec redis redis-cli info memory

# Optimize Redis configuration
echo "maxmemory 256mb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```

#### 3. Application Optimization
```bash
# Scale services
docker-compose -f docker-compose.production.yml up -d --scale backend=3

# Enable caching
export CACHE_ENABLED=true
export CACHE_TTL=3600
```

## Security Best Practices

### 1. Regular Updates
```bash
# Update Docker images
docker-compose -f docker-compose.production.yml pull

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### 2. Access Control
```bash
# Use non-root users
# Already configured in Dockerfiles

# Limit network access
# Configure firewall rules
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Monitoring Security Events
```bash
# Check Grafana security dashboard
# Monitor authentication logs
docker-compose -f docker-compose.production.yml logs backend | grep "Security event"
```

## Support

### Documentation
- **API Documentation**: http://localhost:8000/docs
- **CopilotKit Docs**: https://docs.copilotkit.ai
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph

### Monitoring
- **Health Checks**: Automated health monitoring
- **Alerts**: Configure in Prometheus/Grafana
- **Logs**: Centralized in Elasticsearch

### Backup Strategy
- **Automated**: Daily backups at 2 AM
- **Retention**: 30 days
- **Location**: Local and optional cloud storage

## Development to Production

### Environment Differences
| Feature | Development | Production |
|---------|-------------|------------|
| Debug Mode | Enabled | Disabled |
| Logging | Verbose | Structured |
| Security | Basic | Enterprise |
| Monitoring | Basic | Comprehensive |
| Performance | Optimized for dev | Optimized for production |

### Migration Steps
1. **Export development data**
2. **Update environment variables**
3. **Run production deployment**
4. **Import data**
5. **Verify functionality**
6. **Switch DNS**

## License & Compliance

- **CopilotKit License**: Required for production
- **Data Privacy**: GDPR compliant
- **Security Standards**: OWASP compliant
- **Audit Logs**: Complete audit trail

---

For additional support or questions, refer to the project documentation or contact the development team.
