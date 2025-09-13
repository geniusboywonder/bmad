# BotArmy Deployment Guide

Complete deployment guide for the BotArmy POC application with Sprint 4 production-ready features.

## 🚀 Quick Start

### Simple Deployment

```bash
# Clone repository
git clone <repository-url>
cd bmad

# Deploy to development
./deploy.sh dev

# Deploy to production
./deploy.sh prod

# Health check only
./deploy.sh health-check
```

## 📋 Prerequisites

### System Requirements

- **Python 3.11+**
- **PostgreSQL 12+** 
- **Redis 6+**
- **Docker & Docker Compose** (recommended)
- **Git**

### Environment Setup

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3-pip postgresql redis-server docker.io docker-compose
   
   # macOS (Homebrew)
   brew install python@3.11 postgresql redis docker docker-compose
   
   # CentOS/RHEL
   sudo yum install python3.11 python3-pip postgresql-server redis docker docker-compose
   ```

2. **Verify Installations**
   ```bash
   python3 --version  # Should be 3.11+
   psql --version     # Should be 12+
   redis-cli --version # Should be 6+
   docker --version
   docker-compose --version
   ```

## 🔧 Configuration

### Environment Variables

Create environment files for each deployment environment:

#### Development (.env.dev)
```bash
# Database
DATABASE_URL=postgresql://botarmy_user:password@localhost:5432/botarmy_dev
DATABASE_TEST_URL=postgresql://botarmy_user:password@localhost:5432/botarmy_test

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CELERY_URL=redis://localhost:6379/1

# API
API_BASE_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Security
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
LOG_LEVEL=DEBUG

# Optional LLM Keys (for future use)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

#### Production (.env.prod)
```bash
# Database
DATABASE_URL=postgresql://botarmy_user:secure_password@prod-db:5432/botarmy_prod

# Redis  
REDIS_URL=redis://prod-redis:6379/0
REDIS_CELERY_URL=redis://prod-redis:6379/1

# API
API_BASE_URL=https://api.botarmy.com
CORS_ORIGINS=["https://app.botarmy.com"]

# Security
SECRET_KEY=super-secure-secret-key-generate-new
DEBUG=false
LOG_LEVEL=INFO

# LLM Keys
OPENAI_API_KEY=your-production-openai-key
ANTHROPIC_API_KEY=your-production-anthropic-key
GOOGLE_API_KEY=your-production-google-key
```

## 🐳 Docker Deployment (Recommended)

### Development Environment

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

### Production Environment

```bash
# Start production environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop environment
docker-compose down
```

## 🔨 Manual Deployment

### 1. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createuser -s botarmy_user
sudo -u postgres createdb -O botarmy_user botarmy_prod

# Set password
sudo -u postgres psql -c "ALTER USER botarmy_user WITH PASSWORD 'your_password';"
```

### 2. Application Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 3. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Start FastAPI Server
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🚀 Automated Deployment

### Using Deployment Scripts

The project includes comprehensive deployment automation:

#### Python Deployment Script (deploy.py)

```bash
# Deploy to specific environment
python deploy.py --environment prod

# Run migrations only
python deploy.py --migrate-only --environment prod

# Health check only
python deploy.py --health-check --environment prod

# Skip database backup (development only)
python deploy.py --environment dev --skip-backup
```

#### Shell Script Wrapper (deploy.sh)

```bash
# Make executable
chmod +x deploy.sh

# Deploy to environments
./deploy.sh dev       # Development deployment
./deploy.sh staging   # Staging deployment  
./deploy.sh prod      # Production deployment

# Utility commands
./deploy.sh migrate   # Run migrations only
./deploy.sh health-check  # Health check only
./deploy.sh help      # Show usage
```

### Deployment Features

- **✅ Multi-environment support** (dev/staging/prod)
- **✅ Automated database backups** before deployment
- **✅ Database migration management** with Alembic
- **✅ Health check validation** post-deployment
- **✅ Rollback capabilities** on deployment failure
- **✅ Structured logging** throughout process
- **✅ Performance testing** integration

## 🏥 Health Monitoring

### Health Check Endpoints

| Endpoint | Purpose | Response Time |
|----------|---------|---------------|
| `GET /health/` | Basic health check | < 50ms |
| `GET /health/detailed` | Component status | < 100ms |
| `GET /health/ready` | Readiness probe | < 100ms |
| `GET /health/z` | **Comprehensive monitoring** | < 200ms |

### Health Check Response (Kubernetes-compatible)

```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "BotArmy Backend",
  "version": "0.1.0",
  "timestamp": "2024-09-13T12:00:00Z",
  "checks": {
    "database": "pass|fail",
    "redis": "pass|fail",
    "celery": "pass|fail", 
    "audit_system": "pass|fail"
  },
  "health_percentage": 100.0,
  "services_healthy": "4/4"
}
```

### Monitoring Integration

```bash
# Manual health check
curl http://localhost:8000/health/z

# Kubernetes liveness probe
curl -f http://localhost:8000/health/z || exit 1

# External monitoring
curl -s http://localhost:8000/health/z | jq '.status'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
psql -h localhost -U botarmy_user -d botarmy_prod -c "SELECT 1;"

# View database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connectivity
redis-cli ping

# Check Redis logs
sudo journalctl -u redis -f
```

#### 3. Application Startup Issues
```bash
# Check application logs
docker-compose logs backend

# Check specific service logs
docker-compose logs celery

# Debug mode startup
cd backend
DEBUG=true python -m app.main
```

#### 4. Migration Issues
```bash
# Check migration status
cd backend
alembic current

# View migration history
alembic history

# Manual migration
alembic upgrade head --sql  # Dry run
alembic upgrade head        # Execute
```

### Performance Issues

#### Database Performance
```bash
# Check database performance
psql -U botarmy_user -d botarmy_prod -c "
SELECT schemaname,tablename,attname,n_distinct,correlation 
FROM pg_stats 
WHERE tablename = 'event_log';
"

# Rebuild indexes
psql -U botarmy_user -d botarmy_prod -c "REINDEX TABLE event_log;"
```

#### Application Performance
```bash
# Check API response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health/z

# Monitor WebSocket connections
netstat -an | grep :8000
```

### Recovery Procedures

#### Database Recovery
```bash
# Restore from backup
psql -U botarmy_user -d botarmy_prod -f backup_file.sql

# Rollback deployment
./deploy.sh rollback
```

#### Service Recovery
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend

# Clean restart
docker-compose down
docker-compose up -d
```

## 📊 Performance Monitoring

### Key Metrics

| Metric | Target | Monitoring |
|--------|---------|------------|
| API Response Time | < 200ms | `/health/z` endpoint |
| Database Query Time | < 100ms | Audit query performance |
| WebSocket Latency | < 100ms | Real-time event delivery |
| Health Check Response | < 50ms | Basic health endpoint |

### Monitoring Commands

```bash
# API performance test
ab -n 100 -c 10 http://localhost:8000/health/z

# Database performance
psql -U botarmy_user -d botarmy_prod -c "
EXPLAIN ANALYZE SELECT * FROM event_log 
WHERE project_id = 'uuid-here' 
ORDER BY created_at DESC LIMIT 10;
"

# Redis performance
redis-cli --latency

# System resources
htop
iotop
```

## 🔐 Security Configuration

### Database Security
```sql
-- Create restricted user
CREATE USER botarmy_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE botarmy_prod TO botarmy_readonly;
GRANT USAGE ON SCHEMA public TO botarmy_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO botarmy_readonly;
```

### Application Security
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set secure file permissions
chmod 600 .env.prod
chown www-data:www-data .env.prod
```

### Network Security
```bash
# Firewall rules (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw deny 8000/tcp
```

## 🚀 Production Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Database backup completed
- [ ] SSL certificates valid
- [ ] Firewall rules configured
- [ ] Monitoring alerts configured

### Deployment
- [ ] Run deployment script: `./deploy.sh prod`
- [ ] Verify health checks: `curl /health/z`
- [ ] Run comprehensive test suite: `pytest tests/e2e/test_sprint4* -v`
- [ ] Verify audit trail functionality: `curl /api/v1/audit/events`
- [ ] Check performance metrics (NFR-01 compliance)
- [ ] Validate all 4 audit endpoints are responding

### Post-deployment Validation
- [ ] Monitor application logs
- [ ] Verify WebSocket connectivity
- [ ] Test HITL request workflow with audit logging
- [ ] Validate complete audit trail logging across all operations
- [ ] Confirm backup schedule and audit data retention
- [ ] Run performance validation: `pytest tests/e2e/test_sprint4_full_workflow_e2e.py::TestSprintFourPerformanceValidation -v`

### Quality Assurance Testing
- [ ] **Unit Test Validation**: `pytest tests/unit/test_audit* -v` (13+ core tests)
- [ ] **API Endpoint Testing**: `pytest tests/unit/test_audit_api.py -v` (15+ endpoint tests)  
- [ ] **Integration Testing**: `pytest tests/integration/test_audit_trail_integration.py -v`
- [ ] **Health Monitoring**: `pytest tests/test_health.py::TestHealthzEndpoint -v`
- [ ] **Performance Compliance**: Verify sub-200ms API response times

---

## 📞 Support

For deployment issues:
1. Check troubleshooting section above
2. Review application logs: `docker-compose logs`
3. Check health endpoints: `/health/z`
4. Review deployment script output
5. Validate environment configuration

**Production Deployment Status**: ✅ Ready for production deployment with comprehensive monitoring and automated deployment scripts.