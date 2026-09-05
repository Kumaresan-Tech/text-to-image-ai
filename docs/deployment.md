# Deployment Guide

## Deployment Options

| Option | Best For | Cost | Complexity |
|--------|----------|------|------------|
| Docker Compose (single server) | Small projects, MVP | $20-50/mo | Low |
| AWS ECS Fargate | Production, auto-scaling | $100-500/mo | Medium |
| Vercel (frontend) + EC2 (backend) | Global CDN, easy frontend | $20-100/mo | Low-Medium |
| Kubernetes | Enterprise, high scale | $500+/mo | High |

---

## Option 1: Single EC2 Instance (Recommended for Start)

### Prerequisites
- AWS account with EC2 access
- SSH key pair
- Domain name (optional, for SSL)

### Steps

```bash
# 1. Launch EC2 instance
#    - AMI: Amazon Linux 2023 or Ubuntu 22.04
#    - Instance type: t3.large (2 vCPU, 8GB RAM) minimum
#    - Security group: Open ports 80, 443, 22

# 2. SSH into instance
ssh -i your-key.pem ec2-user@YOUR_EC2_IP

# 3. Install Docker
sudo yum update -y
sudo yum install -y docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# 4. Clone project
cd /opt
sudo git clone https://github.com/yourusername/text2img.git
sudo chown -R ec2-user:ec2-user text2img
cd text2img

# 5. Configure
cp .env.example .env
nano .env  # Fill in all values

# 6. Deploy
docker compose up -d
docker compose exec backend alembic upgrade head

# 7. Verify
docker compose ps
curl http://localhost/api/health
```

### SSL with Certbot

```bash
# Install certbot
sudo yum install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot-renewal
```

---

## Option 2: AWS ECS Fargate

### Prerequisites
- AWS CLI configured
- ECR repositories created
- ECS cluster created
- RDS PostgreSQL instance
- ElastiCache Redis instance
- Secrets Manager with secrets

### Setup

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name text2img-backend
aws ecr create-repository --repository-name text2img-worker
aws ecr create-repository --repository-name text2img-frontend

# 2. Store secrets in Secrets Manager
aws secretsmanager create-secret --name text2img/database-url \
    --secret-string "postgresql+asyncpg://user:pass@your-rds-endpoint:5432/text2img"
# ... repeat for all secrets

# 3. Deploy
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
./deploy/aws/deploy-ecs.sh production
```

### Architecture

```
Internet → ALB → ECS Fargate (backend, worker, frontend)
                    │
                    ├── RDS PostgreSQL (Multi-AZ)
                    ├── ElastiCache Redis
                    └── S3 (image storage)
```

---

## Option 3: Vercel (Frontend) + EC2 (Backend)

### Frontend on Vercel

```bash
cd frontend
npm i -g vercel
vercel login
vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` = https://api.yourdomain.com

### Backend on EC2

```bash
# Follow Option 1 steps for backend + worker only
# Update CORS origins to include Vercel URL
# Update BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

### Vercel Configuration

The `deploy/vercel/vercel.json` configures:
- API rewrites to your backend server
- Security headers
- Health check cron

---

## PostgreSQL Deployment

### Managed (Recommended for Production)

**AWS RDS:**
```bash
aws rds create-db-instance \
    --db-instance-identifier text2img-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 16 \
    --master-username text2img \
    --master-user-password YOUR_PASSWORD \
    --allocated-storage 20 \
    --storage-type gp3 \
    --multi-az \
    --backup-retention-period 7 \
    --no-publicly-accessible
```

**Connection string:**
```
DATABASE_URL=postgresql+asyncpg://text2img:password@your-rds-endpoint:5432/text2img
```

### Self-Hosted (Docker)

The Docker Compose setup includes PostgreSQL with production config at `deploy/postgres/postgresql.conf`:
- `shared_buffers = 256MB`
- `max_connections = 200`
- WAL for crash safety
- Autovacuum tuned for web workloads

---

## Redis Deployment

### Managed

**AWS ElastiCache:**
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id text2img-redis \
    --cache-node-type cache.t3.medium \
    --engine redis \
    --engine-version 7 \
    --num-cache-nodes 1 \
    --security-group-ids sg-xxxx
```

### Self-Hosted (Docker)

The Docker Compose setup includes Redis with `deploy/redis/redis.conf`:
- 256MB memory limit with LRU eviction
- AOF persistence
- Password authentication
- Dangerous commands disabled

---

## Backup & Recovery

### Automated Backup

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /opt/text2img/deploy/scripts/backup-postgres.sh /backups

# Or use Makefile
make backup
```

### Restore

```bash
# List available backups
ls -la backups/

# Restore
make restore FILE=backups/text2img_20260727_020000.sql.gz
```

### S3 Backup (recommended)

```bash
# Sync backups to S3
aws s3 sync /backups s3your-backup-bucket/postgres/ --storage-class STANDARD_IA
```

---

## Monitoring

### Health Checks

```bash
# Full health check
make health

# Manual checks
curl http://localhost/api/health    # Backend
curl http://localhost/health        # Nginx
docker compose ps                   # Container status
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f worker

# Last 100 lines
docker compose logs --tail 100 backend
```

### Sentry Integration

Set `SENTRY_DSN` in `.env` to enable error tracking:
```
SENTRY_DSN=https://xxxx@o000000.ingest.sentry.io/000000
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale worker (more GPU processing)
docker compose up -d --scale worker=3

# Scale backend (more API capacity)
docker compose up -d --scale backend=3
```

### Vertical Scaling

Update `docker-compose.yml` resource limits or upgrade instance type.

---

## Security Checklist

- [ ] Strong `BACKEND_SECRET_KEY` (64+ random characters)
- [ ] Strong database password
- [ ] Strong Redis password
- [ ] HTTPS enabled (Let's Encrypt or ACM)
- [ ] `.env` not committed to version control
- [ ] CORS origins restricted to your domains
- [ ] Rate limiting enabled via Nginx
- [ ] Sentry DSN configured for error tracking
- [ ] Regular database backups
- [ ] S3 bucket with private ACL for image storage
