#!/bin/bash
# ============================================
# AWS EC2 Deployment Script
# ============================================
# Deploys the application to a single EC2 instance
# Prerequisites: SSH access, Docker installed on EC2
#
# Usage: ./deploy-ec2.sh <ec2-host> [key-file]
#   ec2-host: EC2 public IP or hostname
#   key-file: SSH key path (default: ~/.ssh/id_rsa)

set -euo pipefail

EC2_HOST="${1:?Usage: $0 <ec2-host> [key-file]}"
KEY_FILE="${2:-~/.ssh/id_rsa}"
DEPLOY_DIR="/opt/text2img"

echo "╔══════════════════════════════════════╗"
echo "║  AWS EC2 Deploy                      ║"
echo "╚══════════════════════════════════════╝"

# ── Step 1: Upload files ──────────────────────
echo "[1/5] Uploading project files..."
ssh -i "${KEY_FILE}" -o StrictHostKeyChecking=no "ec2-user@${EC2_HOST}" \
    "sudo mkdir -p ${DEPLOY_DIR} && sudo chown ec2-user:ec2-user ${DEPLOY_DIR}"

rsync -avz --delete \
    -e "ssh -i ${KEY_FILE} -o StrictHostKeyChecking=no" \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '__pycache__' \
    --exclude 'storage' \
    --exclude '.env' \
    ./ "ec2-user@${EC2_HOST}:${DEPLOY_DIR}/"

# ── Step 2: Upload env file ───────────────────
echo "[2/5] Uploading environment config..."
if [ -f .env ]; then
    scp -i "${KEY_FILE}" -o StrictHostKeyChecking=no \
        .env "ec2-user@${EC2_HOST}:${DEPLOY_DIR}/.env"
else
    echo "  WARNING: No .env file found. Copy .env.production and configure."
    exit 1
fi

# ── Step 3: Install Docker on EC2 ─────────────
echo "[3/5] Ensuring Docker is installed..."
ssh -i "${KEY_FILE}" -o StrictHostKeyChecking=no "ec2-user@${EC2_HOST}" << 'REMOTE'
if ! command -v docker &> /dev/null; then
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ec2-user
fi
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
REMOTE

# ── Step 4: Build and deploy ──────────────────
echo "[4/5] Building and starting services..."
ssh -i "${KEY_FILE}" -o StrictHostKeyChecking=no "ec2-user@${EC2_HOST}" << REMOTE
cd ${DEPLOY_DIR}
docker compose build
docker compose up -d
echo "Waiting for services to start..."
sleep 15
docker compose exec -T backend alembic upgrade head || echo "Migration skipped (may need manual run)"
REMOTE

# ── Step 5: Verify ────────────────────────────
echo "[5/5] Verifying deployment..."
sleep 5
ssh -i "${KEY_FILE}" -o StrictHostKeyChecking=no "ec2-user@${EC2_HOST}" \
    "cd ${DEPLOY_DIR} && docker compose ps"

echo ""
echo "Deploy complete!"
echo "  URL: http://${EC2_HOST}"
echo "  SSH: ssh -i ${KEY_FILE} ec2-user@${EC2_HOST}"
echo "  Logs: ssh ec2-user@${EC2_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f'"
