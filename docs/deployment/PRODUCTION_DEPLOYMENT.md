# Production Deployment Guide

This guide covers deploying the Financial Dashboard to production using Docker Swarm with proper security and monitoring.

## Prerequisites

- Docker Engine with Swarm mode enabled
- Docker Compose v2+
- At least 4GB RAM and 20GB storage
- SSL certificates (for HTTPS in production)
- Domain name configured

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/docdyhr/financial-dashboard-mcp.git
cd financial-dashboard-mcp

# 2. Set up production secrets
./scripts/setup_production_secrets.sh

# 3. Deploy the stack
docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard

# 4. Check deployment status
docker stack services financial-dashboard
```

## Detailed Deployment Steps

### 1. Environment Setup

#### Initialize Docker Swarm
```bash
# On the manager node
docker swarm init

# On worker nodes (if any)
docker swarm join --token <token> <manager-ip>:2377
```

#### Verify System Requirements
```bash
# Check available resources
docker system df
docker system info

# Ensure adequate disk space
df -h

# Check memory
free -h
```

### 2. Secrets Management

The system uses Docker secrets for secure credential storage:

```bash
# Run the setup script
./scripts/setup_production_secrets.sh
```

This creates the following secrets:
- `secret_key` - Application secret key (64 chars)
- `db_url` - Complete database connection URL
- `db_user` - Database username
- `db_password` - Database password (20 chars)
- `flower_password` - Flower UI password (20 chars)
- `redis_password` - Redis authentication (20 chars)
- `mcp_auth_token` - MCP server authentication (32 chars)

**Important**: Save the generated passwords securely! They are displayed only once.

### 3. Configuration Files

#### Environment Variables
Create a `.env.prod` file (not included in the repository):

```bash
# Application
ENVIRONMENT=production
APP_NAME="Financial Dashboard"
DEBUG=false

# API Keys (optional)
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Logging
LOG_LEVEL=INFO

# Security (these will be overridden by Docker secrets)
JWT_SECRET_KEY=will_be_replaced_by_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### SSL/TLS Configuration
For production HTTPS, configure a reverse proxy:

```nginx
# /etc/nginx/sites-available/financial-dashboard
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://localhost:8502/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Flower (monitoring)
    location /flower/ {
        proxy_pass http://localhost:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Basic auth will be handled by Flower itself
        auth_basic off;
    }
}
```

### 4. Deployment

#### Deploy the Stack
```bash
# Deploy with production configuration
docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard

# Monitor deployment
docker stack services financial-dashboard
docker service logs financial-dashboard_backend
```

#### Verify Deployment
```bash
# Check all services are running
docker stack ps financial-dashboard

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/status

# Test frontend
curl http://localhost:8501/healthz

# Test MCP server
curl http://localhost:8502/health
```

### 5. Database Setup

#### Initialize Database
```bash
# Run migrations
docker exec -it $(docker ps -q -f name=financial-dashboard_backend) \
    alembic upgrade head

# Create initial admin user (optional)
docker exec -it $(docker ps -q -f name=financial-dashboard_backend) \
    python -c "from backend.core.user_setup import create_admin_user; create_admin_user()"
```

#### Database Backup Setup
```bash
# Create backup script
cat > /opt/backup-financial-dashboard.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/financial-dashboard"
mkdir -p "$BACKUP_DIR"

# Database backup
docker exec financial-dashboard_db.1.$(docker service ps -q financial-dashboard_db | head -1) \
    pg_dump -U financial_dashboard financial_dashboard | \
    gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"
EOF

chmod +x /opt/backup-financial-dashboard.sh

# Schedule daily backups
echo "0 2 * * * /opt/backup-financial-dashboard.sh" | crontab -
```

## Monitoring and Maintenance

### Service Monitoring

#### Health Checks
All services include built-in health checks:

```bash
# Check service health
docker service ls
docker service ps financial-dashboard_backend

# View logs
docker service logs financial-dashboard_backend -f
docker service logs financial-dashboard_celery -f
```

#### Flower Monitoring
Access Celery monitoring at `http://your-domain.com/flower/`
- Username: `admin`
- Password: Generated during setup (check saved secrets)

### Log Management

#### Centralized Logging
```bash
# View all logs
docker service logs financial-dashboard_backend

# Real-time logs
docker service logs financial-dashboard_backend -f

# Specific time range
docker service logs financial-dashboard_backend --since 2h
```

#### Log Rotation
Configure log rotation to prevent disk space issues:

```bash
# Configure Docker daemon log rotation
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# Restart Docker
systemctl restart docker
```

### Performance Monitoring

#### Resource Usage
```bash
# Monitor resource usage
docker stats

# Check specific service resources
docker service ps financial-dashboard_backend --format "table {{.Name}}\t{{.CurrentState}}\t{{.Node}}"
```

#### Database Performance
```bash
# Connect to PostgreSQL
docker exec -it $(docker ps -q -f name=financial-dashboard_db) psql -U financial_dashboard

# Check database size and statistics
\l+
\dt+

# Monitor active connections
SELECT * FROM pg_stat_activity;

# Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## Security Considerations

### Network Security
- All services run in an isolated Docker network
- Only necessary ports are exposed
- Use HTTPS in production with proper SSL certificates

### Secret Management
- All sensitive data stored as Docker secrets
- Secrets are encrypted at rest and in transit
- Regular secret rotation recommended

### Access Control
- Flower UI protected with basic authentication
- API endpoints require JWT authentication
- MCP server requires token authentication

### Security Updates
```bash
# Update base images regularly
docker stack rm financial-dashboard
docker image prune -f
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard
```

## Scaling

### Horizontal Scaling
```bash
# Scale backend service
docker service scale financial-dashboard_backend=3

# Scale Celery workers
docker service scale financial-dashboard_celery=2

# Check scaling status
docker service ps financial-dashboard_backend
```

### Database Scaling
For high-load scenarios:
- Configure read replicas
- Implement connection pooling
- Consider database partitioning

### Load Balancing
Use multiple manager nodes for high availability:

```bash
# Add additional manager nodes
docker swarm join-token manager

# Promote worker to manager
docker node promote <node-id>
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service events
docker service ps financial-dashboard_backend --no-trunc

# View detailed logs
docker service logs financial-dashboard_backend --details

# Check resource constraints
docker service inspect financial-dashboard_backend
```

#### Database Connection Issues
```bash
# Test database connectivity
docker exec -it $(docker ps -q -f name=financial-dashboard_backend) \
    python -c "from backend.database import get_db_session; list(get_db_session())"

# Check database logs
docker service logs financial-dashboard_db
```

#### Performance Issues
```bash
# Check system resources
htop
iotop
docker stats

# Monitor database performance
docker exec -it $(docker ps -q -f name=financial-dashboard_db) \
    psql -U financial_dashboard -c "SELECT * FROM pg_stat_activity;"
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop services
docker stack rm financial-dashboard

# Restore from backup
gunzip -c /opt/backups/financial-dashboard/db_backup_TIMESTAMP.sql.gz | \
    docker exec -i $(docker ps -q -f name=postgres) \
    psql -U financial_dashboard financial_dashboard

# Restart services
docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard
```

#### Full System Recovery
```bash
# Backup current state
docker stack rm financial-dashboard

# Clean system
docker system prune -f
docker volume prune -f

# Restore secrets
./scripts/setup_production_secrets.sh

# Redeploy
docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard
```

## Maintenance Schedule

### Daily
- Monitor service health
- Check log files for errors
- Verify backup completion

### Weekly
- Review performance metrics
- Check disk space usage
- Update application if needed

### Monthly
- Rotate secrets
- Update base Docker images
- Review security configurations
- Test backup restoration

## Support and Documentation

### Health Check URLs
- Backend API: `http://localhost:8000/health`
- API Status: `http://localhost:8000/api/v1/status`
- Frontend: `http://localhost:8501/healthz`
- MCP Server: `http://localhost:8502/health`
- Flower: `http://localhost:5555`

### Configuration Files
- Production compose: `docker/docker-compose.prod.yml`
- Development compose: `docker-compose.yml`
- Secrets setup: `scripts/setup_production_secrets.sh`

### Useful Commands
```bash
# Quick status check
docker stack services financial-dashboard

# View all containers
docker stack ps financial-dashboard

# Scale a service
docker service scale financial-dashboard_backend=2

# Update a service
docker service update --image myregistry/backend:latest financial-dashboard_backend

# Remove the entire stack
docker stack rm financial-dashboard
```

This production deployment provides a robust, secure, and scalable foundation for the Financial Dashboard application.
